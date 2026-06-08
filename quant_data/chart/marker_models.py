from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class ChartMarker:
    marker_id: str
    symbol: str
    mode: str
    session_id: str
    timestamp: str
    price: float
    marker_type: str
    side: str = ""
    quantity: int = 0
    label: str = ""
    tooltip: str = ""
    source_ref: str = ""
    order_id: str = ""
    fill_id: str = ""
    signal_id: str = ""
    provenance_id: str = ""
    confidence: float = 0.5
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
