from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any


BANNED_SEARCH_SOURCE_HINTS = (
    "baidu.com",
    "m.baidu.com",
    "so.com",
    "360.cn",
    "sogou.com",
    "wap.sogou.com",
)


@dataclass(slots=True)
class TruthCheckResult:
    accepted: bool
    source_id: str
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DataSourceStatus:
    source_id: str
    source_name: str
    source_url: str = ""
    source_ref: str = ""
    fetched_at: str = ""
    published_at: str = ""
    available_at: str = ""
    ttl_seconds: int = 0
    stale: bool = False
    quality_status: str = "unknown"
    missing_reasons: list[str] = field(default_factory=list)
    raw_hash: str = ""
    unsupported: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SourceStampedData:
    payload: dict[str, Any]
    source: DataSourceStatus

    def to_dict(self) -> dict[str, Any]:
        return {"payload": dict(self.payload), "source": self.source.to_dict()}


def utc_now_text() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")


def raw_hash(value: Any) -> str:
    return sha256(repr(value).encode("utf-8", errors="ignore")).hexdigest()[:16]


def assert_truthful_source(source_id: str = "", source_url: str = "", source_ref: str = "") -> TruthCheckResult:
    text = " ".join([source_id or "", source_url or "", source_ref or ""]).lower()
    reasons: list[str] = []
    for banned in BANNED_SEARCH_SOURCE_HINTS:
        if banned in text:
            reasons.append(f"搜索结果页禁用：{banned}")
    accepted = not reasons
    if not source_id:
        reasons.append("source_id 缺失")
        accepted = False
    return TruthCheckResult(accepted=accepted, source_id=source_id or "missing", reasons=reasons)


def build_source_status(
    *,
    source_id: str,
    source_name: str,
    payload: Any = None,
    source_url: str = "",
    source_ref: str = "",
    fetched_at: str = "",
    published_at: str = "",
    available_at: str = "",
    ttl_seconds: int = 0,
    missing_reasons: list[str] | None = None,
    quality_status: str = "ok",
    unsupported: bool = False,
) -> DataSourceStatus:
    truth = assert_truthful_source(source_id, source_url, source_ref)
    missing = list(missing_reasons or [])
    if not truth.accepted:
        missing.extend(truth.reasons)
    fetched = fetched_at or utc_now_text()
    available = available_at or published_at or fetched
    status = "unsupported" if unsupported else "blocked" if not truth.accepted else quality_status
    return DataSourceStatus(
        source_id=source_id or "missing",
        source_name=source_name or source_id or "未指定",
        source_url=source_url,
        source_ref=source_ref,
        fetched_at=fetched,
        published_at=published_at or available,
        available_at=available,
        ttl_seconds=int(ttl_seconds or 0),
        stale=False,
        quality_status=status,
        missing_reasons=list(dict.fromkeys(missing)),
        raw_hash=raw_hash(payload),
        unsupported=unsupported,
    )
