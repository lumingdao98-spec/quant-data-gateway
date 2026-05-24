from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from quant_data import api
from quant_data.models import Bar
from quant_data.services.cache_state_service import CacheStateService


def _bars(n=12):
    base = datetime(2026, 1, 1)
    return [
        Bar(symbol="300750", frame="1d", ts=base + timedelta(days=i), open=100 + i, high=103 + i, low=99 + i, close=102 + i, volume=1000 + i, amount=1000000 + i, source="mock_daily")
        for i in range(n)
    ]


def test_initial_symbol_300750_returns_complete_daily_bars(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    monkeypatch.setattr(api.service, "get_kline", lambda *args, **kwargs: _bars(12))
    js = TestClient(api.app).get("/api/kline/300750?frame=1d&adjust=none&limit=12&sync_quote=false").json()
    assert js["ok"] is True
    assert js["count"] == 12
    assert all("minute" not in str(x.get("source", "")).lower() for x in js["bars"])


def test_chart_frontend_waits_for_layout_before_drawing():
    html = TestClient(api.app).get("/chart/300750?frame=1d").text
    assert "chartReady" in html
    assert "safeDrawCharts" in html
    assert "ResizeObserver" in html
    assert "r.width>80&&r.height>80" in html
    assert "暂无K线数据" in html
