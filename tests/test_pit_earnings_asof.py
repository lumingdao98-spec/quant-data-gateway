from quant_data.data import EarningsSnapshot, PITStore
from quant_data.events import EventBus


def test_earnings_event_uses_accepted_available_time(tmp_path):
    store = PITStore(tmp_path / "earnings.sqlite")
    event = EarningsSnapshot(
        symbol="688146", report_period="2026H1", report_type="半年度报告", announced_at="2026-07-17T18:00:00",
        accepted_at="2026-07-17T18:03:00", available_at="2026-07-17T18:03:00", net_profit=3.48, consensus_profit=2.5,
        source_id="cninfo", source_name="巨潮资讯",
    ).to_event()
    EventBus(store).publish(event)

    assert store.query_asof(decision_time="2026-07-17T18:02:59", dataset="earnings", symbol="688146") == []
    assert store.query_asof(decision_time="2026-07-17T18:03:00", dataset="earnings", symbol="688146")[0].payload["payload"]["earnings_surprise_pct"] > 0
