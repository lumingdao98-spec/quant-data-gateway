from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api


def test_chart_page_shows_behavior_marker_list_container():
    html = TestClient(api.app).get("/chart/300750?frame=1d").text
    assert "behaviorMarkerList" in html
    assert "K线行为标注" in html
    assert "资金行为/K线标注" in html
    assert "需Level-2确认" in html
    assert "collectAllMarkers" in html
    assert "共 ${markers.length} 条" in html
    assert "chart-grid k-shell" in html
    assert "markerHoverHtml" in html


def test_kline_api_returns_behavior_and_marker_fields():
    data = TestClient(api.app).get("/api/kline/300750?frame=1d&adjust=none&limit=20").json()
    assert "behavior_analysis" in data
    assert "kline_markers" in data
    assert isinstance(data["kline_markers"], list)
