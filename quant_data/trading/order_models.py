from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Literal


OrderMode = Literal["backtest", "realtime_paper", "live"]


ORDER_STATUSES = {
    "signal_created",
    "prechecked",
    "risk_blocked",
    "needs_confirmation",
    "confirmed",
    "submitted",
    "accepted",
    "partially_filled",
    "filled",
    "cancel_requested",
    "cancelled",
    "canceled",
    "rejected",
    "expired",
    "failed",
    "unknown",
    "reconciled",
}


def now_text() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass(slots=True)
class UnifiedOrder:
    order_id: str
    session_id: str
    mode: OrderMode
    symbol: str
    side: str
    order_type: str = "limit"
    quantity: int = 0
    name: str = ""
    broker_order_id: str = ""
    limit_price: float | None = None
    target_weight: float = 0.0
    target_value: float = 0.0
    signal_id: str = ""
    provenance_id: str = ""
    risk_check_id: str = ""
    status: str = "signal_created"
    status_reason: str = ""
    created_at: str = field(default_factory=now_text)
    submitted_at: str = ""
    filled_at: str = ""
    cancelled_at: str = ""
    updated_at: str = field(default_factory=now_text)
    source_page: str = ""
    strategy_family: str = ""
    strategy_profile_hash: str = ""
    policy_hash: str = ""
    execution_profile_version: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class UnifiedFill:
    fill_id: str
    order_id: str
    symbol: str
    side: str
    quantity: int
    price: float
    amount: float
    broker_order_id: str = ""
    broker_trade_id: str = ""
    fee: float = 0.0
    tax: float = 0.0
    slippage: float = 0.0
    filled_at: str = field(default_factory=now_text)
    source: str = ""
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
