from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.services.cache_state_service import CacheStateService


def test_info_analyze_empty_snapshot_id_returns_200_on_fetch_error(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    monkeypatch.setattr(api.info_analysis_service, "analyze", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("network down")))

    res = TestClient(api.app).get("/api/info/analyze/300274?snapshot_id=&name=Sungrow")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["items"] == []
    assert data["errors"]
    assert data["cache_status"]["status"] == "error"
