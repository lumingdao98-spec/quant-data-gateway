from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.services.cache_state_service import CacheStateService


def test_info_snapshot_persists_items_and_items_api_falls_back(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    payload = {
        "snapshot_id": "info-items",
        "symbol": "600438",
        "name": "TW",
        "items": [{"title": "A notice", "source": "cninfo", "summary": "x"}],
        "news": {"count": 1, "items": [{"title": "A notice", "source": "cninfo"}]},
        "source_logs": [{"source": "cache", "status": "ok", "count": 1}],
        "score_model": {"formula": "x"},
    }
    svc.save_info_snapshot("info-items", "600438", payload, mode="light")
    client = TestClient(api.app)
    analyzed = client.get("/api/info/analyze/600438?snapshot_id=info-items&force=false").json()
    assert analyzed["items"][0]["title"] == "A notice"
    paged = client.get("/api/info/items/600438?page=9&page_size=1&include_unknown_date=true").json()
    assert paged["data"]["page"] == 1
    assert paged["data"]["data"][0]["title"] == "A notice"


def test_empty_items_with_raw_count_reports_reason():
    payload = api._normalize_info_payload({"news": {"count": 3, "items": []}}, "600438", "TW", "sid", {"status": "refreshed"}, used_snapshot=False, mode="light")
    assert payload["errors"]
    assert "filtered" in payload["diagnostics"]["filter_empty_reason"] or "empty" in payload["diagnostics"]["filter_empty_reason"]
