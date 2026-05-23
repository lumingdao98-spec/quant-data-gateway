from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.services.cache_state_service import CacheStateService


def _payload(symbol: str = "300274") -> dict:
    return {
        "symbol": symbol,
        "name": "Sungrow",
        "mode": "light",
        "snapshot_id": "info-1",
        "items": [{"title": "official notice", "source": "cninfo"}],
        "grouped_items": [],
        "global_items": [],
        "industry_mapped_items": [],
        "source_logs": [{"source": "cache", "count": 1, "status": "ok", "elapsed_ms": 1, "mode": "light"}],
        "stats": {"item_count": 1},
        "score_model": {"score": 60},
        "diagnostics": {"summary": "cached"},
    }


def test_info_analyze_uses_snapshot_without_refresh(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    svc.save_info_snapshot("info-1", "300274", _payload(), mode="light")

    def fail(*args, **kwargs):
        raise AssertionError("snapshot should be reused")

    monkeypatch.setattr(api.info_analysis_service, "analyze", fail)
    client = TestClient(api.app)
    res = client.get("/api/info/analyze/300274?snapshot_id=info-1&force=false").json()
    assert res["ok"] is True
    assert res["used_snapshot"] is True
    assert res["cache_status"]["status"] == "hit"
    assert res["items"][0]["title"] == "official notice"


def test_info_analyze_empty_snapshot_id_autoloads_latest(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    svc.save_info_snapshot("latest-info", "300274", {**_payload(), "snapshot_id": "latest-info"}, mode="light")

    client = TestClient(api.app)
    res = client.get("/api/info/analyze/300274?snapshot_id=").json()
    assert res["ok"] is True
    assert res["used_snapshot"] is True
    assert res["snapshot_id"] == "latest-info"


def test_info_page_has_empty_cache_and_source_log_containers():
    html = TestClient(api.app).get("/info?symbol=300274&name=Sungrow").text
    assert "V3.18" in html
    assert "cacheStateBox" in html
    assert "sources" in html
    assert "暂无信息" in html
    assert "读取最近快照" in html
