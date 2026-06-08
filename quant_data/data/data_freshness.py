from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class DataFreshnessPolicy:
    ttl_seconds: int = 60
    stale_blocks_buy: bool = True
    allow_hold_reduce_on_stale: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DataFreshnessResult:
    fresh: bool
    stale: bool
    age_seconds: float
    action: str
    reasons: list[str] = field(default_factory=list)
    checked_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_data_freshness(
    fetched_at: str | datetime | None,
    *,
    now: str | datetime | None = None,
    policy: DataFreshnessPolicy | dict[str, Any] | None = None,
) -> DataFreshnessResult:
    cfg = policy if isinstance(policy, DataFreshnessPolicy) else DataFreshnessPolicy(**(policy or {}))
    current = _dt(now) or datetime.now()
    fetched = _dt(fetched_at)
    if fetched is None:
        return DataFreshnessResult(
            fresh=False,
            stale=True,
            age_seconds=0.0,
            action="block_buy",
            reasons=["fetched_at 缺失，不能触发自动买入"],
            checked_at=current.isoformat(timespec="seconds"),
        )
    age = max(0.0, (current - fetched).total_seconds())
    stale = age > cfg.ttl_seconds
    if not stale:
        action = "allow"
        reasons = ["数据在 TTL 内"]
    elif cfg.allow_hold_reduce_on_stale:
        action = "hold_reduce_only"
        reasons = ["数据过期：允许持有/减仓观察，禁止自动新增仓位"]
    else:
        action = "block"
        reasons = ["数据过期：禁止交易"]
    return DataFreshnessResult(
        fresh=not stale,
        stale=stale,
        age_seconds=round(age, 3),
        action=action,
        reasons=reasons,
        checked_at=current.isoformat(timespec="seconds"),
    )


def _dt(value: str | datetime | None) -> datetime | None:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None
