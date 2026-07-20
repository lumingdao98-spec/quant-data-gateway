from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class RealtimeSession:
    session_id: str = field(default_factory=lambda: "paper-" + uuid4().hex[:12])
    symbols: list[str] = field(default_factory=list)
    strategy_family: str = "core_satellite"
    strategy_profile: dict[str, Any] = field(default_factory=dict)
    interval_seconds: int = 15
    status: str = "stopped"
    started_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    paused: bool = False
    kill_switch: bool = False
    config: dict[str, Any] = field(default_factory=dict)
    event_trigger_count: int = 0
    last_event_at: str = ""
    last_sync_at: str = ""
    last_tick_at: str = ""
    last_decision_at: str = ""
    freshness_status: str = "missing"
    data_source_status: str = "尚未收到行情"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
