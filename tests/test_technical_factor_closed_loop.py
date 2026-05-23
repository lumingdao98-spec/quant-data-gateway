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
        last=230,
        pre_close=228,
        open=229,
        high=232,
        low=226,
        volume=300000,
        amount=6e9,
        change=2,
        change_pct=0.88,
        turnover=2.5,
        volume_ratio=1.4,
        pe_dynamic=24,
        pb=5.1,
        total_market_cap=1e12,
        float_market_cap=8e11,
        source="unit",
    )


def _bars(n: int = 120) -> list[Bar]:
    rows = []
    for i in range(n):
        c = 180 + i * 0.45
        rows.append(Bar("300750", "1d", datetime(2026, 1, 1) + timedelta(days=i), c - 1, c + 2, c - 2, c, 200000 + i * 100, c * 2e7, source="unit_daily"))
    return rows


def test_technical_factor_api_returns_40_plus_explained_factors(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    monkeypatch.setattr(api.service, "get_quote", lambda *a, **k: _quote())
    monkeypatch.setattr(api.service, "get_kline", lambda *a, **k: _bars())
    monkeypatch.setattr(api.service, "enrich_quote_metrics", lambda q, **k: q)

    data = TestClient(api.app).get("/api/technical/factors/300750?force=true&limit=120").json()
    assert data["ok"] is True
    assert data["factor_count"] >= 40
    keys = {f["key"] for f in data["factors"]}
    for key in ["ma", "ema", "macd", "rsi", "kdj", "boll", "atr", "vwap", "obv", "mfi", "pivot_points", "support_resistance"]:
        assert key in keys
    for factor in data["factors"]:
        assert {"key", "name", "category", "value", "formula", "params", "signal", "explanation", "score_contribution", "risk_penalty", "applicable_market"} <= set(factor)
    assert data["cache_status"]["status"] == "refreshed"


def test_screener_detail_links_to_technical_factor_matrix():
    html = TestClient(api.app).get("/screener").text
    assert "openTechnicalFactors" in html
    assert "查看技术因子矩阵" in html
