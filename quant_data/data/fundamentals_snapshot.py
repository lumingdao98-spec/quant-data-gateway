from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .data_contracts import DataSourceStatus, build_source_status


REQUIRED_FUNDAMENTAL_FIELDS = (
    "pe",
    "pb",
    "roe",
    "revenue",
    "net_profit",
    "total_market_cap",
    "float_market_cap",
    "industry",
    "is_st",
    "report_date",
)


@dataclass(slots=True)
class FundamentalsSnapshot:
    symbol: str
    fields: dict[str, Any] = field(default_factory=dict)
    source: DataSourceStatus = field(default_factory=lambda: build_source_status(source_id="missing", source_name="基本面源缺失", quality_status="missing"))

    def to_dict(self) -> dict[str, Any]:
        return {"symbol": self.symbol, "fields": dict(self.fields), "source": self.source.to_dict()}


def build_fundamentals_snapshot(symbol: str, data: dict[str, Any] | None, *, source_id: str = "missing", source_name: str = "") -> FundamentalsSnapshot:
    data = dict(data or {})
    missing = [f"{key}字段缺失" for key in REQUIRED_FUNDAMENTAL_FIELDS if data.get(key) in (None, "", "--")]
    source = build_source_status(
        source_id=source_id,
        source_name=source_name or source_id,
        payload=data,
        source_ref=str(data.get("source") or source_id),
        fetched_at=str(data.get("fetched_at") or ""),
        published_at=str(data.get("report_date") or ""),
        available_at=str(data.get("available_at") or data.get("report_date") or ""),
        ttl_seconds=int(data.get("ttl_seconds") or 86_400),
        missing_reasons=missing,
        quality_status="partial" if missing else "ok",
    )
    return FundamentalsSnapshot(symbol=symbol, fields=data, source=source)
