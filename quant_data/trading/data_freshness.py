from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .time_utils import cn_market_now, cn_market_time


@dataclass(slots=True)
class DataFreshnessConfig:
    quote_ttl_seconds: int = 15
    intraday_ttl_seconds: int = 30
    news_ttl_minutes: int = 60
    technical_ttl_minutes: int = 15
    company_profile_ttl_days: int = 7
    critical_fields: tuple[str, ...] = ("quote", "intraday")


@dataclass(slots=True)
class DataFreshnessResult:
    freshness_status: str
    stale_fields: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    action: str = "allow"
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DataFreshnessGuard:
    def __init__(self, config: DataFreshnessConfig | None = None) -> None:
        self.config = config or DataFreshnessConfig()

    def check(self, timestamps: dict[str, Any] | None = None, *, now: datetime | None = None, missing_fields: list[str] | None = None) -> DataFreshnessResult:
        timestamps = timestamps or {}
        now = cn_market_time(now) or cn_market_now()
        stale: list[str] = []
        missing = list(missing_fields or [])
        rules = {
            "quote": timedelta(seconds=self.config.quote_ttl_seconds),
            "intraday": timedelta(seconds=self.config.intraday_ttl_seconds),
            "news": timedelta(minutes=self.config.news_ttl_minutes),
            "technical": timedelta(minutes=self.config.technical_ttl_minutes),
            "company_profile": timedelta(days=self.config.company_profile_ttl_days),
        }
        details: dict[str, Any] = {}
        for field_name, ttl in rules.items():
            raw = timestamps.get(field_name)
            ts = self._parse_time(raw)
            if ts is None:
                missing.append(field_name)
                details[field_name] = {"status": "missing", "ttl_seconds": ttl.total_seconds()}
                continue
            age = now - ts
            is_stale = age > ttl
            if is_stale:
                stale.append(field_name)
            details[field_name] = {
                "status": "stale" if is_stale else "fresh",
                "age_seconds": round(age.total_seconds(), 3),
                "ttl_seconds": ttl.total_seconds(),
                "timestamp": ts.isoformat(timespec="seconds"),
            }
        critical_missing = [x for x in missing if x in self.config.critical_fields]
        critical_stale = [x for x in stale if x in self.config.critical_fields]
        if critical_missing or critical_stale:
            action = "block"
        elif stale:
            action = "reduce"
        elif missing:
            action = "refresh_required"
        else:
            action = "allow"
        status = "fresh" if not stale and not missing else "stale" if stale else "missing"
        return DataFreshnessResult(
            freshness_status=status,
            stale_fields=list(dict.fromkeys(stale)),
            missing_fields=list(dict.fromkeys(missing)),
            action=action,
            checked_at=now.isoformat(timespec="seconds"),
            details=details,
        )

    def _parse_time(self, value: Any) -> datetime | None:
        return cn_market_time(value)
