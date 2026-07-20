from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .data_contracts import DataSourceStatus, build_source_status


@dataclass(slots=True)
class NewsSnapshot:
    symbol: str
    items: list[dict[str, Any]] = field(default_factory=list)
    source: DataSourceStatus = field(
        default_factory=lambda: build_source_status(
            source_id="missing",
            source_name="信息源缺失",
            quality_status="missing",
        )
    )
    available_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "items": list(self.items),
            "source": self.source.to_dict(),
            "available_at": self.available_at or self.source.available_at,
        }


def build_news_snapshot(
    symbol: str,
    items: list[dict[str, Any]] | None,
    *,
    source_id: str = "missing",
    source_name: str = "",
) -> NewsSnapshot:
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    for item in items or []:
        url = str(item.get("url") or item.get("source_url") or "")
        source_ref = str(item.get("source_ref") or url or source_id)
        row_source = build_source_status(
            source_id=str(item.get("source_id") or source_id),
            source_name=str(item.get("source_name") or source_name or source_id),
            payload=item,
            source_url=url,
            source_ref=source_ref,
            fetched_at=str(item.get("fetched_at") or ""),
            published_at=str(item.get("published_at") or item.get("date") or ""),
            available_at=str(item.get("available_at") or ""),
            ttl_seconds=int(item.get("ttl_seconds") or 3600),
        )
        if row_source.quality_status == "blocked":
            missing.append("包含禁用搜索结果页，已剔除")
            continue
        rows.append(
            {
                **dict(item),
                "available_at": row_source.available_at,
                "source_status": row_source.to_dict(),
            }
        )
    if not rows:
        missing.append("没有可用真实信息面数据")
    source = build_source_status(
        source_id=source_id,
        source_name=source_name or source_id,
        payload=rows,
        missing_reasons=missing,
        ttl_seconds=3600,
        quality_status="ok" if rows else "missing",
    )
    available_at = max(
        (str(row.get("available_at") or "") for row in rows),
        default=source.available_at,
    )
    return NewsSnapshot(
        symbol=symbol,
        items=rows,
        source=source,
        available_at=available_at,
    )
