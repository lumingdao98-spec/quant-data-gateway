from fastapi.testclient import TestClient

import quant_data.api as api


def test_closed_market_tick_is_read_only_even_when_client_requests_replay(monkeypatch):
    monkeypatch.setattr(
        api,
        "_market_session",
        lambda market="CN": {
            "market": market,
            "status": "closed",
            "label": "休市",
            "can_refresh": False,
            "now": "2026-07-15T20:00:00",
            "next_refresh_at": "2026-07-16T09:30:00",
        },
    )

    client = TestClient(api.app)
    started = client.post(
        "/api/realtime-paper/sessions/start",
        json={"symbols": ["399989"], "initial_cash": 100000, "reset_account": True},
    ).json()
    session_id = started["session"]["session_id"]
    store = api.realtime_paper_engine_v323.store
    tracked_tables = ("signals", "orders", "fills", "chart_markers", "audit_events", "account_snapshots")
    before = {table: len(store.list(table, mode="realtime_paper", session_id=session_id, limit=2000)) for table in tracked_tables}
    tick_count = api.realtime_paper_engine_v323.engine.state.tick_count

    result = client.post(
        "/api/realtime-paper/tick",
        json={
            "session_id": session_id,
            "symbol": "399989",
            "price": 10,
            "manual_replay": True,
            "is_trading_session": True,
            "technical_score": 90,
            "fundamental_score": 90,
            "information_score": 90,
            "market_score": 90,
        },
    ).json()

    after = {table: len(store.list(table, mode="realtime_paper", session_id=session_id, limit=2000)) for table in tracked_tables}
    assert result["ok"] is True
    assert result["skipped"] is True
    assert result["reason"] == "market_closed"
    assert result["records_written"] is False
    assert result["signal"] is None
    assert result["orders"] == []
    assert result["fills"] == []
    assert result["market_session"]["can_refresh"] is False
    assert api.realtime_paper_engine_v323.engine.state.tick_count == tick_count
    assert after == before


def test_live_tick_ignores_client_replay_override(monkeypatch):
    monkeypatch.setattr(
        api,
        "_market_session",
        lambda market="CN": {
            "market": market,
            "status": "continuous_auction",
            "label": "交易中",
            "can_refresh": True,
            "now": "2026-07-15T10:00:00",
        },
    )
    client = TestClient(api.app)
    started = client.post(
        "/api/realtime-paper/sessions/start",
        json={"symbols": ["399988"], "initial_cash": 100000, "reset_account": True},
    ).json()

    result = client.post(
        "/api/realtime-paper/tick",
        json={
            "session_id": started["session"]["session_id"],
            "symbol": "399988",
            "price": 10,
            "now": "2026-07-15T10:00:00",
            "quote_ts": "2026-07-15T10:00:00",
            "news_ts": "2026-07-15T10:00:00",
            "manual_replay": True,
            "technical_score": 55,
            "fundamental_score": 55,
            "information_score": 55,
            "market_score": 55,
        },
    ).json()

    assert result["ok"] is True
    assert result.get("skipped") is not True
    assert result["market_session"]["can_refresh"] is True
    assert result["signal"]["session_mode"] == "盘中实时"
