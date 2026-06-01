from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


def now_text() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass(slots=True)
class TradingSignal:
    symbol: str
    side: str
    quantity: int = 0
    target_weight: float = 0.0
    price: float | None = None
    score: float = 0.0
    reason: str = ""
    source: str = "manual"
    created_at: str = field(default_factory=now_text)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PaperOrder:
    order_id: str
    symbol: str
    side: str
    quantity: int
    price: float | None
    status: str
    reason: str
    created_at: str = field(default_factory=now_text)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PaperPosition:
    symbol: str
    quantity: int = 0
    avg_cost: float = 0.0
    market_price: float = 0.0
    market_value: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AuditEvent:
    event_type: str
    payload: dict[str, Any]
    created_at: str = field(default_factory=now_text)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
