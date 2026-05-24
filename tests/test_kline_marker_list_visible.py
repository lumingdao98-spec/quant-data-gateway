from fastapi.testclient import TestClient

from quant_data import api


def test_chart_page_exposes_behavior_marker_list():
    html = TestClient(api.app).get("/chart/300750?frame=1d").text
    assert "behaviorMarkerList" in html
    assert "资金行为/K线标注" in html
    assert "klineMarkers" in html


def test_kline_api_contract_has_behavior_fields():
    js = TestClient(api.app).get("/api/kline/300750?frame=1d&limit=8&sync_quote=false").json()
    assert "behavior_analysis" in js
    assert "kline_markers" in js
    assert isinstance(js["kline_markers"], list)
