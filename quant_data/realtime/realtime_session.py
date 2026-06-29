from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class RealtimeSession:
    session_id: str = field(default_factory=lambda: "paper-" + uuid4().hex[:12])
    symbols: list[str] = field(default_factory=list)
    strategy_family: str = "hybrid"
    interval_seconds: int = 15
    status: str = "stopped"
    started_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    paused: bool = False
    kill_switch: bool = False
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
