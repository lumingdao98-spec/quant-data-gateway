from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.models import Bar, Quote
from quant_data.services.cache_state_service import CacheStateService


def _quote() -> Quote:
    return Quote(
        symbol="601012",
        name="LONGi",
        ts=datetime(2026, 5, 23, 10, 0),
        last=10.3,
        pre_close=10.2,
        open=10.4,
        high=12.0,
        low=10.0,
        volume=2600,
        amount=2600000,
        change=0.1,
        change_pct=0.8,
        turnover=3.0,
        volume_ratio=2.4,
        source="unit",
    )


def _bars() -> list[Bar]:
    rows = []
    for i in range(25):
        c = 10 + i * 0.02
        rows.append(Bar("601012", "1d", datetime(2026, 4, 1) + timedelta(days=i), c, c + 0.2, c - 0.2, c, 1000, c * 100000, source="unit_daily"))
    rows[-1] = Bar("601012", "1d", datetime(2026, 5, 1), 10.4, 12.0, 10.0, 10.3, 2600, 2600000, source="unit_daily")
    return rows


def test_kline_api_returns_behavior_analysis_and_markers(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    monkeypatch.setattr(api.service, "get_quote", lambda *a, **k: _quote())
    monkeypatch.setattr(api.service, "get_kline", lambda *a, **k: _bars())

    data = TestClient(api.app).get("/api/kline/601012?frame=1d&limit=25").json()
    assert data["ok"] is True
    assert data["behavior_analysis"]["behavior_tags"]
    assert data["kline_markers"]
    for marker in data["kline_markers"]:
        assert {"date", "type", "label", "price", "tooltip", "evidence"} <= set(marker)
    combined = " ".join(data["behavior_analysis"]["behavior_tags"] + [m["tooltip"] for m in data["kline_markers"]])
    assert "主力对倒" not in combined
    assert "庄家出货" not in combined


def test_chart_page_has_behavior_marker_list():
    html = TestClient(api.app).get("/chart/601012?frame=1d").text
    assert "behaviorMarkerList" in html
    assert "资金行为/K线标注" in html
    assert "need_level2_confirm" in html
