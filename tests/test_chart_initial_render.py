from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.models import Bar, Quote
from quant_data.services.cache_state_service import CacheStateService


def test_initial_300750_kline_returns_complete_bars(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    monkeypatch.setattr(api.service, "get_quote", lambda *a, **k: Quote("300750", "宁德时代", datetime.now(), 200, 198, 199, 205, 196, 1, 1, 2, 1, source="unit"))
    bars = [Bar("300750", "1d", datetime(2026, 1, 1) + timedelta(days=i), 180 + i, 185 + i, 178 + i, 182 + i, 1000 + i, 2e7, source="eastmoney_daily") for i in range(80)]
    monkeypatch.setattr(api.service, "get_kline", lambda *a, **k: bars)

    data = TestClient(api.app).get("/api/kline/300750?frame=1d&adjust=none&limit=80").json()
    assert data["ok"] is True
    assert len(data["bars"]) >= 80
    assert data["bars"][0]["ts"] < data["bars"][-1]["ts"]


def test_chart_frontend_waits_for_layout_before_drawing():
    html = TestClient(api.app).get("/chart/300750?frame=1d").text
    assert "ResizeObserver" in html
    assert "chartReady" in html
    assert "safeDrawCharts" in html
    assert "r.width>280" in html
    assert "K线数量不足" in html
    assert "k-shell" in html
    assert "book.style.display='none'" in html
    assert "rect.width/2" in html
