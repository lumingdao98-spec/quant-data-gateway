from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.services.cache_state_service import CacheStateService


def test_cache_status_api_returns_status_and_clear(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    svc.save_screener_snapshot("screen-1", {"snapshot_id": "screen-1", "results": [{"symbol": "300274"}]})

    client = TestClient(api.app)
    status = client.get("/api/cache/status").json()
    assert status["ok"] is True
    assert "cache_status" in status
    assert any(x["kind"] == "screener_snapshot" and x["count"] == 1 for x in status["items"])

    latest = client.get("/api/cache/screener/latest").json()
    assert latest["ok"] is True
    assert latest["snapshot_id"] == "screen-1"
    assert latest["cache_status"]["status"] == "hit"

    cleared = client.post("/api/cache/clear?kind=screener_snapshot").json()
    assert cleared["ok"] is True
    assert cleared["cleared"] == 1
    assert client.get("/api/cache/screener/latest").json()["ok"] is False
