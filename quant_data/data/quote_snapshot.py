from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .data_contracts import DataSourceStatus, build_source_status


@dataclass(slots=True)
class QuoteSnapshot:
    symbol: str
    name: str = ""
    last: float | None = None
    bid1: float | None = None
    ask1: float | None = None
    amount: float | None = None
    volume: float | None = None
    turnover_rate: float | None = None
    volume_ratio: float | None = None
    change_pct: float | None = None
    limit_up: float | None = None
    limit_down: float | None = None
    orderbook: dict[str, Any] = field(default_factory=dict)
    source: DataSourceStatus = field(default_factory=lambda: build_source_status(source_id="missing", source_name="数据源缺失", quality_status="missing"))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["source"] = self.source.to_dict()
        return data


def build_quote_snapshot(symbol: str, quote: dict[str, Any] | None, *, source_id: str = "missing", source_name: str = "") -> QuoteSnapshot:
    quote = quote or {}
    missing = []
    for key, label in [("last", "最新价"), ("turnover_rate", "换手率"), ("volume_ratio", "量比"), ("orderbook", "盘口深度")]:
        if quote.get(key) in (None, "", "--", {}):
            missing.append(f"{label}字段缺失")
    source = build_source_status(
        source_id=source_id,
        source_name=source_name or source_id or "未指定",
        payload=quote,
        source_ref=str(quote.get("source") or source_id),
        fetched_at=str(quote.get("fetched_at") or quote.get("ts") or ""),
        ttl_seconds=int(quote.get("ttl_seconds") or 15),
        missing_reasons=missing,
        quality_status="partial" if missing else "ok",
    )
    return QuoteSnapshot(
        symbol=symbol,
        name=str(quote.get("name") or ""),
        last=_num_or_none(quote.get("last") or quote.get("price")),
        bid1=_num_or_none(quote.get("bid1")),
        ask1=_num_or_none(quote.get("ask1")),
        amount=_num_or_none(quote.get("amount")),
        volume=_num_or_none(quote.get("volume")),
        turnover_rate=_num_or_none(quote.get("turnover_rate") or quote.get("turnover")),
        volume_ratio=_num_or_none(quote.get("volume_ratio")),
        change_pct=_num_or_none(quote.get("change_pct")),
        limit_up=_num_or_none(quote.get("limit_up") or quote.get("limit_up_price")),
        limit_down=_num_or_none(quote.get("limit_down") or quote.get("limit_down_price")),
        orderbook=dict(quote.get("orderbook") or {}),
        source=source,
    )


def _num_or_none(value: Any) -> float | None:
    try:
        if value in (None, "", "--"):
            return None
        return float(value)
    except Exception:
        return None
