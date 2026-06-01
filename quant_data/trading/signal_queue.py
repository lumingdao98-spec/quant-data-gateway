from __future__ import annotations

from .models import TradingSignal


class SignalQueue:
    def __init__(self) -> None:
        self.items: list[TradingSignal] = []

    def push(self, signal: TradingSignal) -> None:
        self.items.append(signal)

    def list(self) -> list[dict]:
        return [x.to_dict() for x in self.items]
