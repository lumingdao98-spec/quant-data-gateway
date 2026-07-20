from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass(slots=True)
class AccountSnapshot:
    snapshot_id: str
    mode: str
    session_id: str
    account_id: str
    broker: str
    available_cash: float
    frozen_cash: float
    total_cash: float
    position_market_value: float
    total_equity: float
    authorized: bool
    fetched_at: str = field(default_factory=_now)
    available_at: str = field(default_factory=_now)
    source: str = ""
    quality_status: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
