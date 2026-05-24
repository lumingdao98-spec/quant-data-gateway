from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from quant_data import api
from quant_data.models import Bar
from quant_data.services.cache_state_service import CacheStateService


def _bars(n=8):
    base = datetime(2026, 1, 1)
    return [
        Bar(symbol="300750", frame="1d", ts=base + timedelta(days=i), open=10 + i, high=12 + i, low=9 + i, close=11 + i, volume=1000, amount=1000000, source="mock_daily")
        for i in range(n)
    ]


def test_kline_api_writes_and_reads_cache(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    calls = {"n": 0}

    def get_kline(*args, **kwargs):
        calls["n"] += 1
        return _bars()

    monkeypatch.setattr(api.service, "get_kline", get_kline)
    client = TestClient(api.app)
    first = client.get("/api/kline/300750?frame=1d&adjust=none&limit=8&sync_quote=false").json()
    second = client.get("/api/kline/300750?frame=1d&adjust=none&limit=8&sync_quote=false").json()
    assert first["cache_status"]["status"] == "refreshed"
    assert second["cache_status"]["status"] == "hit"
    assert calls["n"] == 1
    assert any(x["kind"] == "kline_cache" and x["count"] == 1 for x in svc.overview()["items"])


def test_chart_page_restores_local_kline_before_network():
    html = TestClient(api.app).get("/chart/300750?frame=1d").text
    assert "quant_last_kline_data" in html
    assert "restoreWatchlistState" in html
    assert "/api/background/refresh/watchlist" in html
