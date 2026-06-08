from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, time
from typing import Any


@dataclass(slots=True)
class MarketSessionStatus:
    is_trading_day: bool
    is_trading_time: bool
    session: str
    next_session_hint: str
    now: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AShareMarketCalendar:
    def status(self, now: datetime | None = None) -> MarketSessionStatus:
        current = now or datetime.now()
        weekday = current.weekday()
        is_day = weekday < 5
        t = current.time()
        morning = time(9, 30) <= t <= time(11, 30)
        afternoon = time(13, 0) <= t <= time(15, 0)
        if not is_day:
            session = "closed"
            hint = "非交易日"
        elif morning or afternoon:
            session = "continuous_auction"
            hint = "盘中连续竞价"
        elif time(11, 30) < t < time(13, 0):
            session = "lunch_break"
            hint = "午间休市，下午 13:00 恢复"
        elif t < time(9, 30):
            session = "pre_open"
            hint = "下一交易时段 09:30"
        else:
            session = "closed"
            hint = "下一交易时段 09:30"
        return MarketSessionStatus(
            is_trading_day=is_day,
            is_trading_time=is_day and (morning or afternoon),
            session=session,
            next_session_hint=hint,
            now=current.isoformat(timespec="seconds"),
        )


def market_session_status(now: datetime | None = None) -> dict[str, Any]:
    return AShareMarketCalendar().status(now).to_dict()
