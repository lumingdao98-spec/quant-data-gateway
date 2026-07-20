from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from hashlib import sha256
import json
from typing import Any

from .data_contracts import assert_truthful_source, raw_hash
from .pit_store import PITRecord


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass(slots=True)
class EventSnapshot:
    event_id: str
    event_type: str
    title: str
    summary: str
    source_id: str
    source_name: str
    published_at: str
    available_at: str
    fetched_at: str
    symbols: list[str] = field(default_factory=list)
    sectors: list[str] = field(default_factory=list)
    markets: list[str] = field(default_factory=list)
    source_url: str = ""
    source_ref: str = ""
    impact_direction: str = "neutral"
    impact_score: float = 0.0
    confidence: float = 0.5
    quality_status: str = "ok"
    missing_reasons: list[str] = field(default_factory=list)
    raw_hash: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    symbol: str = ""
    dataset: str = "events"
    ingested_at: str = ""
    decision_time: str = ""
    severity: str = "info"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_pit_records(self, *, decision_time: str = "") -> list[PITRecord]:
        symbols = self.symbols or [""]
        return [
            PITRecord(
                record_id=f"pit-event-{self.event_id}-{symbol or 'global'}",
                symbol=symbol,
                dataset=self.dataset or "events",
                decision_time=decision_time or self.decision_time or self.available_at,
                available_at=self.available_at,
                payload=self.to_dict(),
                source_id=self.source_id,
            )
            for symbol in symbols
        ]


def build_event_snapshot(payload: dict[str, Any]) -> EventSnapshot:
    data = dict(payload or {})
    fetched_at = str(data.get("fetched_at") or _now())
    published_at = str(data.get("published_at") or "")
    available_at = str(data.get("available_at") or published_at or fetched_at)
    source_id = str(data.get("source_id") or "").strip()
    source_url = str(data.get("source_url") or "")
    source_ref = str(data.get("source_ref") or "")
    truth = assert_truthful_source(source_id, source_url, source_ref)
    missing: list[str] = []
    if not source_id:
        missing.append("source_id 缺失")
    if not data.get("title"):
        missing.append("事件标题缺失")
    if not published_at:
        missing.append("published_at 缺失，available_at 仅能使用抓取时间")
    missing.extend(truth.reasons)
    identity = json.dumps(
        [source_id, data.get("event_type"), data.get("title"), published_at, available_at],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    event_id = str(data.get("event_id") or sha256(identity.encode("utf-8")).hexdigest()[:24])
    clean_payload = dict(data.get("payload") or {})
    return EventSnapshot(
        event_id=event_id,
        event_type=str(data.get("event_type") or "news"),
        title=str(data.get("title") or ""),
        summary=str(data.get("summary") or ""),
        source_id=source_id,
        source_name=str(data.get("source_name") or source_id),
        published_at=published_at,
        available_at=available_at,
        fetched_at=fetched_at,
        symbols=[str(x) for x in (data.get("symbols") or ([data.get("symbol")] if data.get("symbol") else [])) if str(x)],
        sectors=[str(x) for x in data.get("sectors") or [] if str(x)],
        markets=[str(x) for x in data.get("markets") or [] if str(x)],
        source_url=source_url,
        source_ref=source_ref,
        impact_direction=str(data.get("impact_direction") or "neutral"),
        impact_score=max(-100.0, min(100.0, _num(data.get("impact_score")))),
        confidence=max(0.0, min(1.0, _num(data.get("confidence"), 0.5))),
        quality_status="ok" if truth.accepted and not missing else "missing",
        missing_reasons=list(dict.fromkeys(missing)),
        raw_hash=str(data.get("raw_hash") or raw_hash([data, clean_payload])),
        payload=clean_payload,
        symbol=str(data.get("symbol") or ((data.get("symbols") or [""])[0] if data.get("symbols") else "")),
        dataset=str(data.get("dataset") or "events"),
        ingested_at=str(data.get("ingested_at") or fetched_at),
        decision_time=str(data.get("decision_time") or ""),
        severity=str(data.get("severity") or "info"),
        tags=[str(x) for x in data.get("tags") or [] if str(x)],
    )


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except Exception:
        return default
