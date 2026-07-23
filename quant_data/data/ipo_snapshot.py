from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .events_snapshot import EventSnapshot, build_event_snapshot


@dataclass(slots=True)
class IpoSnapshot:
    issuer_symbol: str
    issuer_name: str
    exchange: str
    announced_at: str
    available_at: str
    listing_date: str = ""
    issue_price: float | None = None
    issue_amount: float | None = None
    sectors: list[str] | None = None
    competitors: list[str] | None = None
    source_id: str = ""
    source_name: str = ""
    source_url: str = ""
    ipo_name: str = ""
    market: str = ""
    issue_size: float | None = None
    subscription_date: str = ""
    sector: str = ""
    liquidity_shock_score: float | None = None
    competitor_listing_pressure: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_event(self) -> EventSnapshot:
        return build_event_snapshot(
            {
                "event_type": "ipo",
                "title": f"{self.ipo_name or self.issuer_name or self.issuer_symbol} IPO/上市事件",
                "summary": "IPO 事件只作为行业供给、估值与资金分流证据，不单独触发自动买入。",
                "source_id": self.source_id,
                "source_name": self.source_name,
                "source_url": self.source_url,
                "published_at": self.announced_at,
                "available_at": self.available_at,
                "symbols": [self.issuer_symbol, *(self.competitors or [])],
                "sectors": self.sectors or ([self.sector] if self.sector else []),
                "impact_direction": "neutral",
                "impact_score": max(-100, min(100, -(self.liquidity_shock_score or 0))),
                "payload": self.to_dict(),
                "dataset": "ipo",
                "severity": "important" if abs(self.liquidity_shock_score or 0) >= 60 else "info",
                "tags": ["IPO", self.market or self.exchange],
            }
        )
