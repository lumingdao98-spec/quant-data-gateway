from fastapi.testclient import TestClient

from quant_data import api
from quant_data.services.cache_state_service import CacheStateService


def test_info_page_has_autoload_snapshot_and_local_state():
    html = TestClient(api.app).get("/info?symbol=300274&name=Sungrow").text
    assert "restoreInfoState" in html
    assert "refreshAll(u.get('force')==='true',false)" in html
    assert "quant_info_snapshot_id_" in html
    assert "cacheStateBox" in html
    assert "sources" in html


def test_info_analyze_uses_latest_snapshot_when_url_snapshot_empty(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    payload = {
        "snapshot_id": "info-300274",
        "symbol": "300274",
        "items": [{"title": "公告", "source": "cninfo"}],
        "score_model": {"formula": "test"},
        "source_logs": [{"source": "cache", "count": 1, "status": "ok"}],
    }
    svc.save_info_snapshot("info-300274", "300274", payload)
    js = TestClient(api.app).get("/api/info/analyze/300274?snapshot_id=&force=false").json()
    assert js["ok"] is True
    assert js["used_snapshot"] is True
    assert js["items"]
