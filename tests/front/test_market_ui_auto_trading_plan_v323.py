from fastapi.testclient import TestClient

import quant_data.api as api


def test_ui_exposes_auto_trading_workbench_entry():
    html = TestClient(api.app).get("/ui?symbol=300750&frame=time").text

    assert "/auto-trading" in html
    assert "自动交易总控台" in html
    assert "总控台" in html


def test_intraday_chart_connects_cn_lunch_with_trading_minutes_and_clamps_tooltip():
    html = TestClient(api.app).get("/ui?symbol=300750&frame=time").text

    assert "function isCnLunchGap" in html
    assert "function timeTradeFrac" in html
    assert "function timeTradeX" in html
    assert "function drawSegmentedTimeLine" in html
    assert "breakLunch=false" in html
    assert "timeTradeX(d,w)" in html
    assert "交易分钟连续" in html
    assert "午休按交易分钟压缩连续" in html
    assert "function clampChartTooltip" in html
    assert "Math.min(x,r.right-tw-8)" in html


def test_kline_marker_panel_is_collapsible_and_separate():
    html = TestClient(api.app).get("/chart/300750?frame=1d").text

    assert ".chart-area{display:flex;flex-direction:column" in html
    assert ".chart-grid.k-shell>.chart-grid.k{min-height:760px}" in html
    assert ".marker-list{flex:0 0 auto;position:relative;z-index:6" in html
    assert "function renderMarkerSummaryPanel" in html
    assert "function toggleMarkerPanel" in html
    assert "marker-toggle" in html
    assert "marker-row" in html
    assert "近7日异常/K线标注" in html
