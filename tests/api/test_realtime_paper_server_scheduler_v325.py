from datetime import datetime

import quant_data.api as api


def test_server_scheduler_never_ticks_during_market_close(monkeypatch):
    called = []
    monkeypatch.setattr(
        api,
        "_market_session",
        lambda market="CN": {
            "can_refresh": False,
            "label": "休市",
            "now": "2026-07-20T20:00:00",
        },
    )
    monkeypatch.setattr(api.realtime_paper_engine_v323, "list_sessions", lambda: [{"status": "running"}])
    monkeypatch.setattr(api, "realtime_paper_tick", lambda payload: called.append(payload))

    result = api._run_realtime_paper_sessions_due(now=datetime(2026, 7, 20, 20, 0, 0))

    assert result["status"] == "market_closed"
    assert result["ticks"] == 0
    assert called == []


def test_server_scheduler_ticks_every_symbol_when_session_is_due(monkeypatch):
    called = []
    monkeypatch.setattr(
        api,
        "_market_session",
        lambda market="CN": {
            "can_refresh": True,
            "label": "连续竞价",
            "now": "2026-07-20T10:00:20",
        },
    )
    monkeypatch.setattr(
        api.realtime_paper_engine_v323,
        "list_sessions",
        lambda: [
            {
                "session_id": "paper-v325",
                "status": "running",
                "paused": False,
                "kill_switch": False,
                "symbols": ["300750", "600438"],
                "interval_seconds": 15,
                "last_tick_at": "2026-07-20T10:00:00",
            }
        ],
    )

    def fake_tick(payload):
        called.append(dict(payload))
        return {"ok": True, "orders": [{"order_id": payload["symbol"]}]}

    monkeypatch.setattr(api, "realtime_paper_tick", fake_tick)

    result = api._run_realtime_paper_sessions_due(now=datetime(2026, 7, 20, 10, 0, 20))

    assert result["ok"] is True
    assert result["ticks"] == 2
    assert result["orders"] == 2
    assert [row["symbol"] for row in called] == ["300750", "600438"]
    assert all(row["scheduler_source"] == "server_realtime_paper_scheduler" for row in called)


def test_scheduler_status_explains_next_review_and_market_close(monkeypatch):
    monkeypatch.setattr(
        api,
        "_market_session",
        lambda market="CN": {
            "can_refresh": False,
            "label": "午休",
            "now": "2026-07-20T12:00:00",
        },
    )
    monkeypatch.setattr(
        api.realtime_paper_engine_v323,
        "list_sessions",
        lambda: [
            {
                "session_id": "paper-visible-status",
                "status": "running",
                "symbols": ["300750", "600438"],
                "interval_seconds": 15,
                "last_tick_at": "2026-07-20T11:29:45",
                "last_decision_at": "2026-07-20T11:29:45",
            }
        ],
    )

    result = api.realtime_paper_scheduler_status()

    assert result["active_sessions"] == 0
    assert result["due_sessions"] == 0
    assert result["sessions"][0]["symbol_count"] == 2
    assert result["sessions"][0]["symbols"] == ["300750", "600438"]
    assert result["sessions"][0]["blocked_reason"] == "休市或午休待机"
    assert result["sessions"][0]["next_due_at"] is None
