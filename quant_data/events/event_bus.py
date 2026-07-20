from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from quant_data.data.events_snapshot import EventSnapshot
from quant_data.data.pit_store import PITStore


EventHandler = Callable[[EventSnapshot], Any]


class EventBus:
    def __init__(self, pit_store: PITStore | None = None) -> None:
        self.pit_store = pit_store
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers[str(event_type or "*")].append(handler)

    def publish(self, event: EventSnapshot) -> list[Any]:
        if self.pit_store is not None:
            for record in event.to_pit_records():
                self.pit_store.put(record)
        results: list[Any] = []
        for handler in [*self._handlers.get(event.event_type, []), *self._handlers.get("*", [])]:
            results.append(handler(event))
        return results
