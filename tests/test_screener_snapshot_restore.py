from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.services.cache_state_service import CacheStateService


def test_screener_run_persists_snapshot_and_latest_restore(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    monkeypatch.setattr(api.score_history_service, "save_results", lambda data, mode="balanced": len(data))
    monkeypatch.setattr(
        api.screener_service,
        "run",
        lambda config: {
            "ok": True,
            "data": [{"symbol": "300274", "name": "Sungrow", "grade": "B", "total_score": 72, "tags": [], "risk_flags": []}],
            "result_count": 1,
            "universe_count": 1,
            "analyzed_count": 1,
            "elapsed_seconds": 0.01,
            "error_count": 0,
        },
    )

    client = TestClient(api.app)
    ran = client.get("/api/screener/run?symbols=300274&max_items=1&enable_news=false").json()
    sid = ran["screener_snapshot_id"]
    assert sid
    assert ran["cache_status"]["status"] == "refreshed"

    snap = client.get(f"/api/screener/snapshot/{sid}").json()
    assert snap["ok"] is True
    assert snap["results"][0]["symbol"] == "300274"

    latest = client.get("/api/cache/screener/latest").json()
    assert latest["ok"] is True
    assert latest["snapshot_id"] == sid


def test_screener_page_has_restore_controls_and_local_state_keys():
    client = TestClient(api.app)
    html = client.get("/screener").text
    assert "V3.18" in html
    assert "恢复上次筛选" in html
    assert "重新筛选" in html
    assert "清空本地状态" in html
    assert "qdg_screener_snapshot_id" in html
    assert "qdg_screener_selected_symbol" in html
    assert "qdg_screener_scroll_top" in html
