from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .realtime_session import RealtimeSession


@dataclass(slots=True)
class RealtimeRuntimeState:
    session: RealtimeSession = field(default_factory=RealtimeSession)
    last_tick_at: str = ""
    data_freshness: dict[str, Any] = field(default_factory=dict)
    message: str = "未启动"

    def to_dict(self) -> dict[str, Any]:
        return {"session": self.session.to_dict(), "last_tick_at": self.last_tick_at, "data_freshness": dict(self.data_freshness), "message": self.message}
