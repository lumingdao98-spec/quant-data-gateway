from __future__ import annotations

from dataclasses import asdict, dataclass, field
import os
from typing import Any


@dataclass(slots=True)
class BrokerConfig:
    broker_type: str = "disabled"
    live_trading_enabled: bool = False
    feature_live_broker: bool = False
    order_confirm_required: bool = True
    live_kill_switch: bool = False
    trade_whitelist_symbols: list[str] = field(default_factory=list)
    max_live_order_value: float = 50_000.0
    max_daily_live_order_count: int = 5
    max_daily_loss_pct: float = 0.03
    qmt_path: str = ""
    qmt_account_id: str = ""
    qmt_account_type: str = ""
    qmt_session_id: str = ""
    ptrade_path: str = ""
    ptrade_account_id: str = ""
    ptrade_module: str = "ptrade"
    ptrade_client_factory: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_broker_config(env: dict[str, str] | None = None) -> BrokerConfig:
    data = env or os.environ
    return BrokerConfig(
        broker_type=data.get("BROKER_TYPE", "disabled").lower(),
        live_trading_enabled=_bool(data.get("LIVE_TRADING_ENABLED"), False),
        feature_live_broker=_bool(data.get("FEATURE_LIVE_BROKER"), False),
        order_confirm_required=_bool(data.get("ORDER_CONFIRM_REQUIRED"), True),
        live_kill_switch=_bool(data.get("LIVE_KILL_SWITCH"), False),
        trade_whitelist_symbols=_csv(data.get("TRADE_WHITELIST_SYMBOLS", "")),
        max_live_order_value=float(data.get("MAX_LIVE_ORDER_VALUE") or 50_000),
        max_daily_live_order_count=int(data.get("MAX_DAILY_LIVE_ORDER_COUNT") or 5),
        max_daily_loss_pct=float(data.get("MAX_DAILY_LOSS_PCT") or 0.03),
        qmt_path=data.get("QMT_PATH", ""),
        qmt_account_id=data.get("QMT_ACCOUNT_ID", ""),
        qmt_account_type=data.get("QMT_ACCOUNT_TYPE", ""),
        qmt_session_id=data.get("QMT_SESSION_ID", ""),
        ptrade_path=data.get("PTRADE_PATH", ""),
        ptrade_account_id=data.get("PTRADE_ACCOUNT_ID", ""),
        ptrade_module=data.get("PTRADE_MODULE", "ptrade"),
        ptrade_client_factory=data.get("PTRADE_CLIENT_FACTORY", ""),
    )


def _csv(value: str) -> list[str]:
    text = str(value or "").replace("，", ",").replace("；", ",").replace(";", ",").replace("\n", ",")
    return [item.strip() for item in text.split(",") if item.strip()]


def _bool(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
