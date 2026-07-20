from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .events_snapshot import EventSnapshot, build_event_snapshot


@dataclass(slots=True)
class EarningsSnapshot:
    symbol: str
    report_period: str
    announced_at: str
    available_at: str
    revenue: float | None = None
    net_profit: float | None = None
    revenue_growth_pct: float | None = None
    profit_growth_pct: float | None = None
    consensus_profit: float | None = None
    guidance_low: float | None = None
    guidance_high: float | None = None
    source_id: str = ""
    source_name: str = ""
    source_url: str = ""
    report_type: str = ""
    filing_date: str = ""
    accepted_at: str = ""
    yoy: float | None = None
    qoq: float | None = None
    eps: float | None = None
    estimate: float | None = None
    surprise: float | None = None
    guidance: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_event(self) -> EventSnapshot:
        surprise = self.surprise
        if surprise is None and self.net_profit is not None and self.consensus_profit not in (None, 0):
            surprise = (self.net_profit - self.consensus_profit) / abs(self.consensus_profit) * 100
        return build_event_snapshot(
            {
                "event_type": "earnings",
                "title": f"{self.symbol} 财务报告 {self.report_period}",
                "summary": "业绩数据已按公告可得时间记录，历史决策只能读取 available_at 之前数据。",
                "source_id": self.source_id,
                "source_name": self.source_name,
                "source_url": self.source_url,
                "published_at": self.accepted_at or self.announced_at or self.filing_date,
                "available_at": self.available_at,
                "symbols": [self.symbol],
                "impact_direction": "positive" if (surprise or 0) > 0 else "negative" if (surprise or 0) < 0 else "neutral",
                "impact_score": max(-100, min(100, surprise or 0)),
                "payload": {**self.to_dict(), "earnings_surprise_pct": surprise},
                "dataset": "earnings",
                "severity": "important" if abs(surprise or 0) >= 20 else "info",
                "tags": ["财报", self.report_type or "业绩"],
            }
        )
