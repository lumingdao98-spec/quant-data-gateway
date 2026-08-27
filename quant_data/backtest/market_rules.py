from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any


DEFAULT_RULE_PATH = Path(__file__).resolve().parents[2] / "config" / "market_rules" / "a_share_rules.yaml"


@dataclass(slots=True)
class RuleProfile:
    profile_id: str
    exchange: str
    board: str
    security_type: str = "stock"
    effective_from: str = "1900-01-01"
    effective_to: str | None = None
    t_plus_one: bool = True
    lot_size_buy: int = 100
    odd_lot_sell_once: bool = True
    price_limit_pct: float = 0.10
    ipo_first_n_days_no_limit: int = 0
    price_tick: float = 0.01
    order_types_allowed: tuple[str, ...] = ("next_open", "next_close", "vwap", "limit")
    same_day_roundtrip_rule: str = "forbidden"
    source: str = "config"
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["order_types_allowed"] = list(self.order_types_allowed)
        return data


class MarketRuleEngine:
    """Resolve effective A-share/ETF trading rules from config and security master."""

    def __init__(self, profiles: dict[str, RuleProfile] | None = None, *, version: str = "", timezone: str = "Asia/Shanghai") -> None:
        self.profiles = profiles or {}
        self.version = version
        self.timezone = timezone

    @classmethod
    def default(cls) -> "MarketRuleEngine":
        return cls.from_file(DEFAULT_RULE_PATH)

    @classmethod
    def from_file(cls, path: str | Path) -> "MarketRuleEngine":
        parsed = _parse_limited_yaml(Path(path))
        profiles = {
            key: _profile_from_mapping(key, value)
            for key, value in (parsed.get("profiles") or {}).items()
            if isinstance(value, dict)
        }
        return cls(profiles, version=str(parsed.get("version") or ""), timezone=str(parsed.get("timezone") or "Asia/Shanghai"))

    @classmethod
    def from_dict(cls, profiles: dict[str, dict[str, Any]]) -> "MarketRuleEngine":
        return cls({key: _profile_from_mapping(key, value) for key, value in profiles.items()})

    def resolve_profile(
        self,
        symbol: str,
        *,
        asof: str | date | datetime | None = None,
        security_master: dict[str, Any] | None = None,
        profile_id: str | None = None,
    ) -> RuleProfile:
        security_master = security_master or {}
        pid = profile_id or security_master.get("price_limit_profile_id") or security_master.get("rule_profile_id")
        if not pid:
            pid = self.infer_profile_id(symbol, security_master)
        candidates = [p for key, p in self.profiles.items() if key == pid and _effective(p, asof)]
        if candidates:
            return candidates[-1]
        fallback = self.profiles.get("SZSE_MAIN") or next(iter(self.profiles.values()), None)
        if fallback:
            data = fallback.to_dict()
            data.update({"profile_id": fallback.profile_id, "source": "config:fallback", "warnings": [f"未找到规则 {pid}，回退 {fallback.profile_id}"]})
            return RuleProfile(**{**data, "order_types_allowed": tuple(data.get("order_types_allowed") or [])})
        return RuleProfile(profile_id="UNSPECIFIED", exchange="", board="", source="missing", warnings=["未指定规则配置"])

    def infer_profile_id(self, symbol: str, security_master: dict[str, Any] | None = None) -> str:
        security_master = security_master or {}
        security_type = str(security_master.get("security_type") or security_master.get("asset_type") or "").lower()
        board = str(security_master.get("board") or "").upper()
        exchange = str(security_master.get("exchange") or "").upper()
        risk = bool(security_master.get("risk_warning_status") or security_master.get("is_st"))
        settlement = str(
            security_master.get("sellable_cycle")
            or security_master.get("settlement_cycle")
            or security_master.get("trading_cycle")
            or ""
        ).upper().replace(" ", "")
        same_day_sellable = security_master.get("t_plus_one") is False or settlement in {"T+0", "T0", "0"}
        if exchange in {"HKEX", "SEHK", "HK"}:
            return "HK_EQUITY_T0"
        if exchange in {"NYSE", "NASDAQ", "AMEX", "US"}:
            return "US_EQUITY_T0"
        if security_type in {"etf", "fund"}:
            return "ETF_T0" if same_day_sellable else "ETF_GENERIC"
        if board in {"STAR", "SSE_STAR"}:
            return "SSE_STAR"
        if board in {"CHINEXT", "SZSE_CHINEXT"}:
            return "SZSE_CHINEXT"
        if board in {"BSE", "BJSE"} or exchange in {"BSE", "BJSE"}:
            return "BSE_STOCK"
        if risk and exchange == "SSE":
            return "SSE_MAIN_RISK_WARNING"
        if risk and exchange == "SZSE":
            return "SZSE_MAIN_RISK_WARNING"
        text = str(symbol or "")
        if text.startswith(("51", "15", "16", "58")):
            return "ETF_GENERIC"
        if text.startswith(("688", "689")):
            return "SSE_STAR"
        if text.startswith(("300", "301")):
            return "SZSE_CHINEXT"
        if text.startswith(("8", "4", "920")):
            return "BSE_STOCK"
        if text.startswith("6"):
            return "SSE_MAIN_RISK_WARNING" if risk else "SSE_MAIN"
        return "SZSE_MAIN_RISK_WARNING" if risk else "SZSE_MAIN"


def _effective(profile: RuleProfile, asof: str | date | datetime | None) -> bool:
    if not asof:
        return True
    text = asof.date().isoformat() if isinstance(asof, datetime) else asof.isoformat() if isinstance(asof, date) else str(asof)[:10]
    if profile.effective_from and text < profile.effective_from:
        return False
    if profile.effective_to and text > profile.effective_to:
        return False
    return True


def _profile_from_mapping(profile_id: str, data: dict[str, Any]) -> RuleProfile:
    allowed = data.get("order_types_allowed", ("next_open", "next_close", "vwap", "limit"))
    if isinstance(allowed, str):
        allowed = tuple(x.strip() for x in allowed.split(",") if x.strip())
    return RuleProfile(
        profile_id=profile_id,
        exchange=str(data.get("exchange") or ""),
        board=str(data.get("board") or ""),
        security_type=str(data.get("security_type") or "stock"),
        effective_from=str(data.get("effective_from") or "1900-01-01"),
        effective_to=str(data.get("effective_to")) if data.get("effective_to") else None,
        t_plus_one=bool(data.get("t_plus_one", True)),
        lot_size_buy=int(float(data.get("lot_size_buy") or 100)),
        odd_lot_sell_once=bool(data.get("odd_lot_sell_once", True)),
        price_limit_pct=float(data.get("price_limit_pct") or 0.10),
        ipo_first_n_days_no_limit=int(float(data.get("ipo_first_n_days_no_limit") or 0)),
        price_tick=float(data.get("price_tick") or data.get("order_price_tick") or 0.01),
        order_types_allowed=tuple(allowed),
        same_day_roundtrip_rule=str(data.get("same_day_roundtrip_rule") or "forbidden"),
        source="config",
    )


def _parse_limited_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"profiles": {}}
    root: dict[str, Any] = {"profiles": {}}
    current: dict[str, Any] | None = None
    in_profiles = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith(" "):
            key, _, value = line.partition(":")
            key = key.strip()
            if key == "profiles":
                in_profiles = True
                continue
            root[key] = _parse_scalar(value.strip())
            continue
        if in_profiles and line.startswith("  ") and not line.startswith("    ") and line.strip().endswith(":"):
            pid = line.strip()[:-1]
            current = {}
            root["profiles"][pid] = current
            continue
        if current is not None and line.startswith("    "):
            key, _, value = line.strip().partition(":")
            current[key.strip()] = _parse_scalar(value.strip())
    return root


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"", "null", "None"}:
        return None
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value
