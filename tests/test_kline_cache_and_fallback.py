from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.models import Bar, Quote
from quant_data.services.cache_state_service import CacheStateService


def _quote() -> Quote:
    return Quote(
        symbol="300750",
        name="CATL",
        ts=datetime(2026, 5, 23, 10, 0),
        last=200.0,
        pre_close=198.0,
        open=199.0,
        high=201.0,
        low=197.0,
        volume=100000,
        amount=2e9,
        change=2.0,
        change_pct=1.0,
        source="unit",
    )


def _bars(n: int = 8, source: str = "eastmoney_daily") -> list[Bar]:
    return [
        Bar("300750", "1d", datetime(2026, 5, 1) + timedelta(days=i), 190 + i, 193 + i, 188 + i, 191 + i, 1000 + i, 2e7 + i, source=source)
        for i in range(n)
    ]


def test_daily_kline_failure_does_not_use_sina_minute_as_daily(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    monkeypatch.setattr(api.service, "get_quote", lambda *a, **k: _quote())
    monkeypatch.setattr(api.service, "get_kline", lambda *a, **k: _bars(source="sina_minute"))

    data = TestClient(api.app).get("/api/kline/300750?frame=1d&limit=8").json()
    assert data["ok"] is False
    assert data["bars"] == []
    assert data["cache_status"]["status"] == "error"


def test_kline_failure_returns_stale_cache_when_available(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    key = api._kline_key("300750", "1d", "none", 8)
    svc.put("kline_cache", key, {"ok": True, "bars": [b.to_dict() for b in _bars(8)], "source": ["cache"]}, ttl_seconds=-1, symbol="300750")
    monkeypatch.setattr(api.service, "get_quote", lambda *a, **k: _quote())
    monkeypatch.setattr(api.service, "get_kline", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("daily down")))

    data = TestClient(api.app).get("/api/kline/300750?frame=1d&limit=8").json()
    assert data["ok"] is True
    assert data["stale_cache_used"] is True
    assert data["cache_status"]["status"] == "stale"
    assert data["bars"]


def test_chart_page_has_kline_error_and_cache_status_containers():
    html = TestClient(api.app).get("/chart/300750?frame=1d").text
    assert "behaviorMarkerList" in html
    assert "K线缓存状态/错误" in html
    assert "cache_status" in html
