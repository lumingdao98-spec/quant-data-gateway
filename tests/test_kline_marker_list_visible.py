from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.models import Quote


def test_chart_page_shows_behavior_marker_list_container():
    html = TestClient(api.app).get("/chart/300750?frame=1d").text
    assert "behaviorMarkerList" in html
    assert "K线行为标注" in html
    assert "资金行为/K线标注" in html
    assert "需Level-2确认" in html
    assert "collectAllMarkers" in html
    assert "近7日 ${markers.length}/${allMarkers.length} 条" in html
    assert "chart-grid k-shell" in html
    assert "markerHoverHtml" in html


def test_kline_api_returns_behavior_and_marker_fields():
    data = TestClient(api.app).get("/api/kline/300750?frame=1d&adjust=none&limit=20").json()
    assert "behavior_analysis" in data
    assert "kline_markers" in data
    assert isinstance(data["kline_markers"], list)


def test_detail_limit_applies_to_cached_payload(monkeypatch):
    rows = []
    for i in range(30):
        close = 10 + i * 0.02
        rows.append({
            "symbol": "601012",
            "frame": "1d",
            "ts": (datetime(2026, 4, 1) + timedelta(days=i)).isoformat(),
            "open": close,
            "high": close + 0.2,
            "low": close - 0.2,
            "close": close,
            "volume": 1000,
            "amount": close * 100000,
            "turnover": 0.5,
            "change_pct": 0.2,
            "source": "unit_cache",
        })
    quote = Quote(
        symbol="601012",
        name="Unit",
        ts=datetime(2026, 5, 1),
        last=rows[-1]["close"],
        pre_close=rows[-2]["close"],
        open=rows[-1]["open"],
        high=rows[-1]["high"],
        low=rows[-1]["low"],
        volume=rows[-1]["volume"],
        amount=rows[-1]["amount"],
        change=rows[-1]["close"] - rows[-2]["close"],
        change_pct=0.2,
        source="unit",
    )

    monkeypatch.setattr(
        api,
        "_safe_kline_payload",
        lambda *a, **k: {
            "ok": True,
            "bars": rows,
            "source": ["unit_cache"],
            "fallback_chain": ["unit"],
            "errors": [],
            "cache_status": {"status": "stale"},
            "stale_cache_used": True,
        },
    )
    monkeypatch.setattr(api, "_enrich_quote_real", lambda *a, **k: (quote, quote.to_dict(), {"status": "unit"}))

    data = TestClient(api.app).get("/api/detail/601012?frame=1d&limit=14&adjust=none").json()

    assert data["count"] == 14
    assert len(data["bars"]) == 14
