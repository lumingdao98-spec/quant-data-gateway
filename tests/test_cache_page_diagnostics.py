from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.services.cache_state_service import CacheStateService


def test_cache_overview_includes_diagnostic_keys(tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    svc.put("quote_cache", "300274", {"quote": {"symbol": "300274"}}, ttl_seconds=-1, symbol="300274")
    overview = svc.overview()
    quote = next(x for x in overview["items"] if x["kind"] == "quote_cache")
    assert "last_write_key" in quote
    assert "last_read_key" in quote
    assert "recent_miss_reason" in quote
    assert "recent_error" in quote
    assert "diagnostic" in quote


def test_cache_page_exposes_diagnostics():
    html = TestClient(api.app).get("/cache").text
    assert "V3.18.1 Cache Diagnostics" in html
    assert "Last write key" in html
    assert "miss/error diagnostic" in html
    assert "kline_cache is zero" in html
