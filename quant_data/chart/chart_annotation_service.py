from __future__ import annotations

from collections import defaultdict
from typing import Any

from .marker_models import ChartMarker
from .trading_marker_engine import TradingMarkerEngine


class ChartAnnotationService:
    def __init__(self) -> None:
        self.engine = TradingMarkerEngine()
        self._markers: dict[str, list[ChartMarker]] = defaultdict(list)

    def add_marker(self, marker: ChartMarker) -> dict[str, Any]:
        self._markers[marker.symbol].append(marker)
        return marker.to_dict()

    def add_order(self, order: dict[str, Any]) -> dict[str, Any]:
        return self.add_marker(self.engine.from_order(order))

    def add_fill(self, fill: dict[str, Any], *, mode: str = "paper", session_id: str = "") -> dict[str, Any]:
        return self.add_marker(self.engine.from_fill(fill, mode=mode, session_id=session_id))

    def list_markers(self, symbol: str, *, mode: str | None = None, limit: int = 300) -> list[dict[str, Any]]:
        rows = list(self._markers.get(symbol, []))
        if mode:
            rows = [x for x in rows if x.mode == mode]
        return [x.to_dict() for x in rows[-max(1, int(limit or 300)) :]]

    def rebuild(self, symbol: str, *, orders: list[dict[str, Any]] | None = None, fills: list[dict[str, Any]] | None = None, mode: str = "backtest") -> list[dict[str, Any]]:
        self._markers[symbol] = []
        for order in orders or []:
            if str(order.get("symbol") or "") == symbol:
                self.add_order({**order, "mode": order.get("mode") or mode})
        for fill in fills or []:
            if str(fill.get("symbol") or "") == symbol:
                self.add_fill(fill, mode=mode, session_id=str(fill.get("session_id") or ""))
        return self.list_markers(symbol)
