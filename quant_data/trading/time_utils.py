from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


CN_MARKET_TIMEZONE = ZoneInfo("Asia/Shanghai")


def cn_market_time(value: Any) -> datetime | None:
    """Parse a timestamp and return a timezone-free China market datetime."""
    if isinstance(value, datetime):
        parsed = value
    elif value in (None, ""):
        return None
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(CN_MARKET_TIMEZONE)
    return parsed.replace(tzinfo=None)


def cn_market_now() -> datetime:
    return datetime.now(CN_MARKET_TIMEZONE).replace(tzinfo=None)
