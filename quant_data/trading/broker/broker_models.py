from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


def now_text() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass(slots=True)
class BrokerConnectionStatus:
    connected: bool
    status: str
    broker: str = "disabled"
    message: str = ""
    live_trading_enabled: bool = False
    order_confirm_required: bool = True
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BrokerCash:
    available_cash: float = 0.0
    frozen_cash: float = 0.0
    total_cash: float = 0.0
    currency: str = "CNY"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BrokerPosition:
    symbol: str
    name: str = ""
    quantity: int = 0
    available_quantity: int = 0
    avg_cost: float = 0.0
    market_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    source: str = ""
    fetched_at: str = field(default_factory=now_text)
    available_at: str = ""
    quality_status: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BrokerAccountSnapshot:
    account_id: str = ""
    broker: str = "disabled"
    cash: BrokerCash = field(default_factory=BrokerCash)
    positions: list[BrokerPosition] = field(default_factory=list)
    fetched_at: str = field(default_factory=now_text)
    authorized: bool = False
    source: str = ""
    available_at: str = ""
    quality_status: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id,
            "broker": self.broker,
            "cash": self.cash.to_dict(),
            "positions": [x.to_dict() for x in self.positions],
            "fetched_at": self.fetched_at,
            "authorized": self.authorized,
            "source": self.source,
            "available_at": self.available_at or self.fetched_at,
            "quality_status": self.quality_status,
        }


@dataclass(slots=True)
class LiveOrderRequest:
    symbol: str
    side: str
    quantity: int
    order_type: str = "limit"
    limit_price: float | None = None
    target_weight: float = 0.0
    strategy_family: str = ""
    signal_id: str = ""
    provenance_id: str = ""
    risk_check_id: str = ""
    confirm_id: str = ""
    source_page: str = "live-trading"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class LiveOrderAck:
    accepted: bool
    status: str
    order_id: str = ""
    broker_order_id: str = ""
    reason: str = ""
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BrokerOrder:
    order_id: str
    symbol: str
    side: str
    status: str
    quantity: int = 0
    price: float | None = None
    created_at: str = field(default_factory=now_text)
    raw_response: dict[str, Any] = field(default_factory=dict)
    broker_order_id: str = ""
    filled_quantity: int = 0
    updated_at: str = field(default_factory=now_text)
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BrokerTrade:
    trade_id: str
    order_id: str
    symbol: str
    side: str
    quantity: int
    price: float
    amount: float
    filled_at: str = field(default_factory=now_text)
    raw_response: dict[str, Any] = field(default_factory=dict)
    broker_order_id: str = ""
    fee: float = 0.0
    tax: float = 0.0
    slippage: float = 0.0
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CancelOrderResult:
    ok: bool
    order_id: str
    status: str
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
