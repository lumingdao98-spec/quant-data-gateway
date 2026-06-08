from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_broker_config(env: dict[str, str] | None = None) -> BrokerConfig:
    e = env or os.environ
    return BrokerConfig(
        broker_type=e.get("BROKER_TYPE", "disabled").lower(),
        live_trading_enabled=_bool(e.get("LIVE_TRADING_ENABLED"), False),
        feature_live_broker=_bool(e.get("FEATURE_LIVE_BROKER"), False),
        order_confirm_required=_bool(e.get("ORDER_CONFIRM_REQUIRED"), True),
        live_kill_switch=_bool(e.get("LIVE_KILL_SWITCH"), False),
        trade_whitelist_symbols=[x.strip() for x in e.get("TRADE_WHITELIST_SYMBOLS", "").replace("，", ",").split(",") if x.strip()],
        max_live_order_value=float(e.get("MAX_LIVE_ORDER_VALUE") or 50_000),
        max_daily_live_order_count=int(e.get("MAX_DAILY_LIVE_ORDER_COUNT") or 5),
        max_daily_loss_pct=float(e.get("MAX_DAILY_LOSS_PCT") or 0.03),
        qmt_path=e.get("QMT_PATH", ""),
        qmt_account_id=e.get("QMT_ACCOUNT_ID", ""),
        qmt_account_type=e.get("QMT_ACCOUNT_TYPE", ""),
        qmt_session_id=e.get("QMT_SESSION_ID", ""),
        ptrade_path=e.get("PTRADE_PATH", ""),
        ptrade_account_id=e.get("PTRADE_ACCOUNT_ID", ""),
    )


def _bool(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
