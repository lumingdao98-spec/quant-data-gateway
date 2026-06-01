from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.models import Quote
from quant_data.services.cache_state_service import CacheStateService


def test_quote_cache_stale_can_backfill_closed_market_fields(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    q = Quote("300750", "CATL", datetime(2026, 5, 22, 15), 200, 198, 199, 205, 196, 1000, 2e8, 2, 1, turnover=2.3, volume_ratio=1.2, pe_dynamic=25, pb=4, total_market_cap=900_000_000_000, float_market_cap=700_000_000_000, source="unit")
    svc.put("quote_cache", "300750", {"quote": api._quote_dict_with_aliases(q)}, ttl_seconds=-1, symbol="300750", source="unit")
    monkeypatch.setattr(api.service, "get_quote", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down")))

    data = TestClient(api.app).get("/api/quote/300750").json()["data"]
    assert data["pe_ttm"] == 25
    assert data["pb"] == 4
    assert data["total_market_cap"] == 900_000_000_000
    assert data["quote_cache_status"]["status"] == "stale"


def test_ui_metric_card_shows_sources_and_missing_reasons():
    html = TestClient(api.app).get("/ui").text
    assert "metric_sources" in html
    assert "metric_missing_reasons" in html
    assert "数据源缺失/F10未返回" in html
    assert "休市无盘口" in html
