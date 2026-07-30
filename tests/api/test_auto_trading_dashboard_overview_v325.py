from fastapi.testclient import TestClient

from quant_data import api


def _patch_dashboard_dependencies(monkeypatch, *, records_factory=None):
    calls = {
        "live_sync": 0,
        "account_synced": [],
        "positions_synced": [],
        "scheduler_sessions": [],
    }
    broker = {
        "ok": True,
        "broker": {"broker": "disabled", "status": "disabled", "connected": False},
        "config": {"broker_type": "disabled"},
        "safety": {
            "LIVE_TRADING_ENABLED": False,
            "ORDER_CONFIRM_REQUIRED": True,
            "LIVE_KILL_SWITCH": False,
        },
    }
    synced = {
        "account": {},
        "positions": [],
        "cash": {},
        "broker": broker["broker"],
        "data_available": False,
    }

    def sync_live_account_state():
        calls["live_sync"] += 1
        return synced

    def account_response(value):
        calls["account_synced"].append(value)
        return {"ok": True, "data": {"available_cash": 0}, "data_available": False}

    def positions_response(value):
        calls["positions_synced"].append(value)
        return {"ok": True, "data": [], "count": 0, "summary": {}}

    def records(limit=200, **_kwargs):
        if records_factory is not None:
            return records_factory(limit)
        calls["records_limit"] = limit
        return {"ok": True, "data": [{"id": "record-1"}], "count": 1, "summary": {"rows_count": 1}}

    monkeypatch.setattr(api, "live_broker_status", lambda: broker)
    monkeypatch.setattr(api.live_trading_engine_v323, "sync_live_account_state", sync_live_account_state)
    monkeypatch.setattr(api, "_live_account_response", account_response)
    monkeypatch.setattr(api, "_live_positions_response", positions_response)
    session_rows = [{"session_id": "paper-1", "status": "running"}]
    monkeypatch.setattr(
        api,
        "realtime_paper_sessions",
        lambda: {"ok": True, "data": session_rows},
    )
    monkeypatch.setattr(api, "trading_records_v323", records)
    monkeypatch.setattr(
        api,
        "_data_center_status_payload",
        lambda broker_status=None: {
            "ok": True,
            "trading_store": {"tables": {"orders": 1}},
            "broker": broker_status or {},
        },
    )
    monkeypatch.setattr(api, "live_confirm_queue", lambda: {"ok": True, "data": [], "count": 0})
    monkeypatch.setattr(
        api,
        "auto_trading_config_get",
        lambda: {"ok": True, "data": {"symbols": ["300750"], "strategy_combo": ["score_driven"]}},
    )
    monkeypatch.setattr(api, "_auto_trading_readiness", lambda config: {"ok": True, "gates": {"symbols": bool(config["symbols"])}})
    monkeypatch.setattr(
        api,
        "live_position_reviews",
        lambda symbol="", limit=200: {"ok": True, "data": [], "count": 0, "limit": limit},
    )
    monkeypatch.setattr(
        api,
        "position_review_scheduler_status",
        lambda: {"ok": True, "data": {"due": False}, "last_run": {}, "order_execution": False},
    )
    monkeypatch.setattr(
        api,
        "_realtime_paper_scheduler_status",
        lambda rows=None: (
            calls["scheduler_sessions"].append(rows),
            {"ok": True, "enabled": True, "running": True, "sessions": rows or []},
        )[1],
    )
    return calls, synced


def test_auto_trading_dashboard_overview_aggregates_core_state_with_one_live_sync(monkeypatch):
    calls, synced = _patch_dashboard_dependencies(monkeypatch)

    payload = TestClient(api.app).get(
        "/api/auto-trading/dashboard-overview",
        params={"records_limit": 999},
    ).json()

    assert payload["ok"] is True
    assert payload["partial"] is False
    assert payload["component_errors"] == []
    assert payload["generated_at"]
    assert "不会生成信号、订单、成交" in payload["truth_boundary"]
    assert calls["live_sync"] == 1
    assert calls["account_synced"] == [synced]
    assert calls["positions_synced"] == [synced]
    assert calls["records_limit"] == 200
    assert calls["scheduler_sessions"] == [
        [{"session_id": "paper-1", "status": "running"}]
    ]
    assert payload["data"]["records"]["summary"]["rows_count"] == 1
    assert payload["data"]["data_center"]["broker"]["status"] == "disabled"
    assert payload["data"]["readiness"]["gates"]["symbols"] is True
    assert payload["data"]["live_reviews"]["limit"] == 50
    assert set(payload["timings_ms"]) >= {
        "broker",
        "live_sync",
        "sessions",
        "records",
        "data_center",
        "queue",
        "live_account",
        "live_positions",
        "auto_config",
        "readiness",
        "live_reviews",
        "review_schedule",
        "paper_schedule",
    }


def test_auto_trading_dashboard_overview_keeps_partial_results(monkeypatch):
    def failed_records(_limit):
        raise RuntimeError("records unavailable")

    calls, _synced = _patch_dashboard_dependencies(
        monkeypatch,
        records_factory=failed_records,
    )

    payload = TestClient(api.app).get("/api/auto-trading/dashboard-overview").json()

    assert payload["ok"] is True
    assert payload["partial"] is True
    assert payload["data"]["records"] == {
        "ok": False,
        "data": [],
        "count": 0,
        "summary": {},
    }
    assert payload["component_errors"] == [
        {"key": "records", "error": "records unavailable"}
    ]
    assert calls["live_sync"] == 1
