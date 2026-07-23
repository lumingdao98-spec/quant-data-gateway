from datetime import datetime

from quant_data.trading.position_review_scheduler import PositionReviewScheduler


def test_scheduler_runs_once_after_close_on_trading_day():
    scheduler = PositionReviewScheduler()

    before = scheduler.decide(now=datetime(2026, 7, 23, 14, 59), last_run_date="")
    due = scheduler.decide(now=datetime(2026, 7, 23, 15, 6), last_run_date="")
    repeated = scheduler.decide(now=datetime(2026, 7, 23, 15, 30), last_run_date="2026-07-23")

    assert before.due is False
    assert due.due is True
    assert due.review_date == "2026-07-23"
    assert repeated.due is False
    assert "跳过重复" in repeated.reason


def test_scheduler_skips_weekend_and_exposes_next_run():
    scheduler = PositionReviewScheduler()
    decision = scheduler.decide(now=datetime(2026, 7, 25, 16, 0), last_run_date="")

    assert decision.due is False
    assert "非交易日" in decision.reason
    assert decision.next_run_at.startswith("2026-07-27T15:05:00")


def test_scheduler_force_is_explicit_and_does_not_depend_on_exchange_clock():
    scheduler = PositionReviewScheduler()
    decision = scheduler.decide(now=datetime(2026, 7, 25, 9, 0), last_run_date="2026-07-24", force=True)

    assert decision.due is True
    assert decision.reason == "人工强制复核"
