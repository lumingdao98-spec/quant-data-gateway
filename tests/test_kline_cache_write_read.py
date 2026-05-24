from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.models import Bar, Quote
from quant_data.services.cache_state_service import CacheStateService


def _quote() -> Quote:
    return Quote("300750", "CATL", datetime(2026, 5, 22, 15), 200, 198, 199, 202, 197, 1000, 2e8, 2, 1, source="unit")


def _bars(n: int = 8, source: str = "eastmoney_daily") -> list[Bar]:
    return [Bar("300750", "1d", datetime(2026, 5, 1) + timedelta(days=i), 190 + i, 195 + i, 188 + i, 192 + i, 1000 + i, 2e7, source=source) for i in range(n)]


def test_kline_success_writes_and_second_read_hits_cache(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    calls = {"kline": 0}
    monkeypatch.setattr(api.service, "get_quote", lambda *a, **k: _quote())

    def fake_kline(*args, **kwargs):
        calls["kline"] += 1
        return _bars()

    monkeypatch.setattr(api.service, "get_kline", fake_kline)
    client = TestClient(api.app)
    first = client.get("/api/kline/300750?frame=1d&adjust=none&limit=8").json()
    second = client.get("/api/kline/300750?frame=1d&adjust=none&limit=8").json()
    assert first["ok"] is True
    assert first["cache_status"]["status"] == "refreshed"
    assert second["cache_status"]["status"] == "hit"
    assert calls["kline"] == 1
    overview = client.get("/api/cache/status").json()
    kline = next(x for x in overview["items"] if x["kind"] == "kline_cache")
    assert kline["count"] >= 1
    assert kline["last_write_key"] == "300750:1d:none"
