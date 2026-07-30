from quant_data.api import _realtime_paper_scheduler_wait_seconds


def test_scheduler_keeps_one_second_checks_for_active_sessions():
    assert _realtime_paper_scheduler_wait_seconds(
        {"status": "complete", "sessions_checked": 2}
    ) == 1.0


def test_scheduler_backs_off_without_active_sessions():
    assert _realtime_paper_scheduler_wait_seconds(
        {"status": "complete", "sessions_checked": 0}
    ) == 10.0


def test_scheduler_uses_bounded_market_closed_wait():
    assert _realtime_paper_scheduler_wait_seconds(
        {
            "status": "market_closed",
            "market_session": {"seconds_to_next_refresh": 3600},
        }
    ) == 30.0
    assert _realtime_paper_scheduler_wait_seconds(
        {
            "status": "market_closed",
            "market_session": {"seconds_to_next_refresh": 3},
        }
    ) == 3.0

