from __future__ import annotations

from typing import Any

from .models import AuditEvent


class AuditLog:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(self, event_type: str, payload: dict[str, Any]) -> AuditEvent:
        event = AuditEvent(event_type=event_type, payload=payload)
        self.events.append(event)
        return event

    def list(self, limit: int = 200) -> list[dict[str, Any]]:
        return [x.to_dict() for x in self.events[-max(1, int(limit or 200)) :]][::-1]
