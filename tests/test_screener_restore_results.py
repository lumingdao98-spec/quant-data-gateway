from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.services.cache_state_service import CacheStateService


def _row(symbol: str = "300750", grade: str = "B") -> dict:
    return {
        "symbol": symbol,
        "name": "Test",
        "grade": grade,
        "total_score": 72,
        "manual_review_score": 70,
        "candidate_channels": ["custom_input"],
        "last": 10,
        "change_pct": 1.2,
    }


def test_screener_run_snapshot_restores_full_results(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    monkeypatch.setattr(api, "_merge_screener_item_quote_metrics", lambda item, force=False: item)
    monkeypatch.setattr(
        api.screener_service,
        "run",
        lambda config: {"ok": True, "data": [_row("300750"), _row("600519")], "result_count": 2, "analyzed_count": 2, "error_count": 0},
    )

    client = TestClient(api.app)
    run = client.get("/api/screener/run?symbols=300750,600519&selected_symbol=600519&view_mode=full&scroll_position=123").json()
    sid = run["screener_snapshot_id"]
    assert run["results"]
    assert run["selected_symbol"] == "600519"
    assert run["selected_row"]["symbol"] == "600519"

    snap = client.get(f"/api/screener/snapshot/{sid}").json()
    assert snap["ok"] is True
    assert snap["restored"] is True
    assert len(snap["results"]) == 2
    assert snap["view_mode"] == "full"
    assert snap["scroll_position"] == 123

    latest = client.get("/api/cache/screener/latest").json()
    assert latest["ok"] is True
    assert latest["results"][0]["symbol"] == "300750"

    payload = latest["snapshot"]
    svc.put("screener_snapshot", sid, payload, ttl_seconds=-1, source="test")
    stale = client.get(f"/api/screener/snapshot/{sid}").json()
    assert stale["cache_status"]["status"] == "stale"
    assert stale["results"]


def test_empty_screener_snapshot_is_not_marked_restored(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    svc.save_screener_snapshot("empty", {"snapshot_id": "empty", "results": [], "summary": {}})
    res = TestClient(api.app).get("/api/screener/snapshot/empty").json()
    assert res["ok"] is True
    assert res["restored"] is False
    assert "no results" in res["message"]
