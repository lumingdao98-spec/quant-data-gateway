from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class RealtimeScheduler:
    interval_seconds: int = 15
    manual_only: bool = False

    def next_delay(self, *, is_trading_time: bool) -> int | None:
        if self.manual_only or not is_trading_time:
            return None
        return max(5, min(60, int(self.interval_seconds or 15)))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
