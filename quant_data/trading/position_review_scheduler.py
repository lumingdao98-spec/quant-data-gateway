from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from quant_data.market_calendar import MarketCalendar


@dataclass(frozen=True, slots=True)
class PositionReviewScheduleDecision:
    due: bool
    reason: str
    review_date: str
    last_run_date: str
    next_run_at: str
    checked_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PositionReviewScheduler:
    """Decide when held positions need one post-close review.

    The scheduler only decides and records due state. The caller owns position
    loading and review execution, so this class can never place an order.
    """

    def __init__(
        self,
        calendar: MarketCalendar | None = None,
        *,
        review_time: time = time(15, 5),
        timezone: str = "Asia/Shanghai",
    ) -> None:
        self.calendar = calendar or MarketCalendar()
        self.review_time = review_time
        self.timezone = ZoneInfo(timezone)

    def decide(
        self,
        *,
        now: datetime | None = None,
        last_run_date: str = "",
        force: bool = False,
    ) -> PositionReviewScheduleDecision:
        current = self._local(now)
        today = current.date()
        trading_day = not self.calendar.is_holiday("CN", today)
        review_date = today.isoformat() if trading_day else ""

        if force:
            return PositionReviewScheduleDecision(
                due=True,
                reason="人工强制复核",
                review_date=review_date or today.isoformat(),
                last_run_date=last_run_date,
                next_run_at=self._next_run_after(today).isoformat(timespec="seconds"),
                checked_at=current.isoformat(timespec="seconds"),
            )

        due_at = datetime.combine(today, self.review_time, tzinfo=self.timezone)
        if not trading_day:
            reason = "非交易日，等待下一交易日收盘后复核"
            due = False
        elif current < due_at:
            reason = "尚未到收盘后复核时间"
            due = False
        elif last_run_date == review_date:
            reason = "当日持仓已复核，跳过重复运行"
            due = False
        else:
            reason = "交易日收盘后持仓复核到期"
            due = True

        next_run = due_at if trading_day and current < due_at else self._next_run_after(today)
        return PositionReviewScheduleDecision(
            due=due,
            reason=reason,
            review_date=review_date,
            last_run_date=last_run_date,
            next_run_at=next_run.isoformat(timespec="seconds"),
            checked_at=current.isoformat(timespec="seconds"),
        )

    def _local(self, now: datetime | None) -> datetime:
        if now is None:
            return datetime.now(self.timezone)
        if now.tzinfo is None:
            return now.replace(tzinfo=self.timezone)
        return now.astimezone(self.timezone)

    def _next_run_after(self, day: date) -> datetime:
        candidate = day + timedelta(days=1)
        for _ in range(370):
            if not self.calendar.is_holiday("CN", candidate):
                return datetime.combine(candidate, self.review_time, tzinfo=self.timezone)
            candidate += timedelta(days=1)
        return datetime.combine(candidate, self.review_time, tzinfo=self.timezone)
