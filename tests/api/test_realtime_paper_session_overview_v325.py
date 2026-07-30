from fastapi.testclient import TestClient

from quant_data import api


def test_realtime_paper_session_overview_aggregates_existing_panels(monkeypatch):
    session_id = "paper-overview-test"

    monkeypatch.setattr(
        api,
        "realtime_paper_session_get",
        lambda value: {"ok": True, "data": {"session_id": value, "status": "running"}},
    )
    monkeypatch.setattr(
        api,
        "realtime_paper_session_orders",
        lambda value, limit=200: {
            "ok": True,
            "data": [{"order_id": "order-1"}],
            "count": 1,
            "session_id": value,
            "limit": limit,
        },
    )
    monkeypatch.setattr(
        api,
        "realtime_paper_session_fills",
        lambda value, limit=200: {
            "ok": True,
            "data": [{"fill_id": "fill-1"}],
            "count": 1,
            "session_id": value,
            "limit": limit,
        },
    )
    monkeypatch.setattr(
        api,
        "realtime_paper_session_positions",
        lambda value: {
            "ok": True,
            "data": {"snapshot": {"cash": 90000}, "positions": [{"symbol": "300750"}]},
            "summary": {"equity": 100000},
            "session_id": value,
        },
    )
    monkeypatch.setattr(
        api,
        "realtime_paper_session_markers",
        lambda value: {
            "ok": True,
            "data": [{"marker_id": f"marker-{index}"} for index in range(4)],
            "count": 4,
            "session_id": value,
        },
    )
    monkeypatch.setattr(
        api,
        "realtime_paper_session_audit",
        lambda value, limit=300: {
            "ok": True,
            "data": [{"event_id": "audit-1"}],
            "count": 1,
            "session_id": value,
            "limit": limit,
        },
    )
    monkeypatch.setattr(
        api,
        "realtime_paper_position_reviews",
        lambda value, symbol="", limit=200: {
            "ok": True,
            "data": [{"symbol": "300750"}],
            "count": 1,
            "session_id": value,
            "limit": limit,
        },
    )

    payload = TestClient(api.app).get(
        f"/api/realtime-paper/sessions/{session_id}/overview",
        params={
            "orders_limit": 11,
            "fills_limit": 12,
            "markers_limit": 2,
            "audit_limit": 13,
            "reviews_limit": 14,
        },
    ).json()

    assert payload["ok"] is True
    assert payload["session_id"] == session_id
    assert payload["data"]["snapshot"]["data"]["status"] == "running"
    assert payload["data"]["orders"]["limit"] == 11
    assert payload["data"]["fills"]["limit"] == 12
    assert payload["data"]["audit"]["limit"] == 13
    assert payload["data"]["reviews"]["limit"] == 14
    assert payload["data"]["positions"]["summary"]["equity"] == 100000
    assert payload["data"]["markers"]["count"] == 2
    assert len(payload["data"]["markers"]["data"]) == 2
    assert payload["counts"] == {
        "orders": 1,
        "fills": 1,
        "markers": 2,
        "audit": 1,
        "reviews": 1,
    }
    assert payload["generated_at"]


def test_realtime_paper_session_overview_stops_when_session_is_missing(monkeypatch):
    monkeypatch.setattr(
        api,
        "realtime_paper_session_get",
        lambda value: {"ok": False, "data": None, "engine": None},
    )

    payload = TestClient(api.app).get(
        "/api/realtime-paper/sessions/missing-session/overview"
    ).json()

    assert payload == {
        "ok": False,
        "session_id": "missing-session",
        "message": "实时模拟会话不存在",
        "data": {"snapshot": {"ok": False, "data": None, "engine": None}},
    }
