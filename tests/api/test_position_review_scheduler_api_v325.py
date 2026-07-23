from fastapi.testclient import TestClient

import quant_data.api as api


def test_forced_position_review_scheduler_reviews_paper_and_skips_disconnected_live(monkeypatch):
    stored = []
    monkeypatch.setattr(api, "_latest_position_review_run", lambda: {})
    monkeypatch.setattr(
        api.realtime_paper_engine_v323,
        "list_sessions",
        lambda: [{"session_id": "paper-1", "status": "running"}, {"session_id": "old", "status": "stopped"}],
    )
    monkeypatch.setattr(
        api,
        "_review_realtime_paper_positions",
        lambda session_id: {"ok": True, "session_id": session_id, "held_count": 2, "count": 2},
    )
    monkeypatch.setattr(
        api.live_trading_engine_v323,
        "status",
        lambda: {"ok": True, "broker": {"connected": False, "broker": "disabled"}},
    )
    monkeypatch.setattr(api.trading_store_v323, "put", lambda table, payload, **kwargs: stored.append((table, payload)) or kwargs.get("record_id", "id"))

    response = TestClient(api.app).post("/api/position-reviews/scheduler/run-due", json={"force": True})
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "complete"
    assert body["data"]["paper_reviewed_count"] == 2
    assert body["data"]["live_reviewed_count"] == 0
    assert body["data"]["broker_submitted"] is False
    assert {table for table, _ in stored} == {"position_review_runs", "audit_events"}
