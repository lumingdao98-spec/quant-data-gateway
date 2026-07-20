from quant_data.data.events_snapshot import build_event_snapshot
from quant_data.events import EventTriggerEngine


def test_event_trigger_blocks_future_and_major_negative_buy():
    event = build_event_snapshot({
        "event_id": "e1", "event_type": "announcement", "title": "重大风险公告", "source_id": "cninfo",
        "published_at": "2026-07-20T10:00:00", "available_at": "2026-07-20T10:05:00",
        "impact_direction": "negative", "impact_score": -90, "confidence": 0.9,
    })
    engine = EventTriggerEngine()

    future = engine.evaluate(event, decision_time="2026-07-20T10:04:59", strategy_family="short")
    current = engine.evaluate(event, decision_time="2026-07-20T10:05:00", strategy_family="short")
    assert future.passed is False
    assert current.action == "risk_block"
