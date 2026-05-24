from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.models import Bar, Quote
from quant_data.services.cache_state_service import CacheStateService


def test_daily_kline_rejects_minute_source_without_cache(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    monkeypatch.setattr(api.service, "get_quote", lambda *a, **k: Quote("300750", "CATL", datetime.now(), 200, 198, 199, 201, 197, 1, 1, 2, 1))
    bars = [Bar("300750", "1d", datetime(2026, 5, 1) + timedelta(days=i), 1, 2, 1, 2, 1, 1, source="sina_minute") for i in range(8)]
    monkeypatch.setattr(api.service, "get_kline", lambda *a, **k: bars)
    data = TestClient(api.app).get("/api/kline/300750?frame=1d&adjust=none&limit=8").json()
    assert data["ok"] is False
    assert data["bars"] == []
    assert "minute" in ";".join(data["errors"]).lower()
    overview = TestClient(api.app).get("/api/cache/status").json()
    kline = next(x for x in overview["items"] if x["kind"] == "kline_cache")
    assert kline["count"] == 0
    assert kline["recent_error"]
