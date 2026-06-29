from fastapi.testclient import TestClient

import quant_data.api as api


def test_ui_exposes_auto_trading_workbench_entry():
    client = TestClient(api.app)
    html = client.get("/ui?symbol=300750&frame=time").text

    assert "/auto-trading" in html
    assert "auto-trading" in html
    assert "config/one-click" in client.get("/auto-trading").text


def test_intraday_chart_uses_compressed_lunch_axis_and_clamps_tooltip():
    html = TestClient(api.app).get("/ui?symbol=300750&frame=time").text

    assert "function isCnLunchGap" in html
    assert "function isCnLunchMinutePoint" in html
    assert "function timeTradeFrac" in html
    assert "function timeTradeX" in html
    assert "function drawSegmentedTimeLine" in html
    assert "lunchStart=11*60+30,lunchEnd=13*60,end=15*60+30" in html
    assert "11:30/13:00" in html
    assert "交易分钟连续" in html
    assert "午休压缩" in html
    assert "drawSegmentedTimeLine(ctx,data,d=>d.price,(d)=>timeTradeX(d,w),y,'#d1d5db',2,false)" in html
    assert "function clampChartTooltip" in html
    assert "Math.min(x,r.right-tw-8)" in html
    assert "markerBox.style.display=isTimeMode()?'none':'block'" in html
    assert "if(isTimeMode())return;e.preventDefault()" in html


def test_kline_marker_panel_is_collapsible_and_separate():
    html = TestClient(api.app).get("/chart/300750?frame=1d").text

    assert ".chart-area{display:flex;flex-direction:column" in html
    assert "qd-chart-final-overflow-guard" in html
    assert ".chart-grid.k-shell>.chart-grid.k{min-height:880px" in html
    assert ".marker-list{position:relative;z-index:auto" in html
    assert ".qd:hover b{display:block;max-height:92px;overflow:auto}" in html
    assert "function renderMarkerSummaryPanel" in html
    assert "function toggleMarkerPanel" in html
    assert "marker-toggle" in html
    assert "marker-row" in html
    assert "近7日异常/K线标注" in html
