from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class LiveSession:
    session_id: str = field(default_factory=lambda: "live-" + uuid4().hex[:12])
    status: str = "disabled"
    broker: str = "disabled"
    started_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    kill_switch: bool = False
    message: str = "真实交易默认关闭"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
