from fastapi.testclient import TestClient

import quant_data.api as api


def test_ui_exposes_auto_trading_workbench_entry():
    client = TestClient(api.app)
    html = client.get("/ui?symbol=300750&frame=time").text

    assert "/auto-trading" in html
    assert "auto-trading" in html
    assert "config/one-click" in client.get("/auto-trading").text


def test_ui_embedded_mode_for_auto_trading_iframe():
    html = TestClient(api.app).get("/ui?symbol=300750&frame=time&embedded=1").text

    assert "const EMBEDDED_MODE=true" in html
    assert ".app.embedded" in html
    assert "qd-auto-iframe-fit-guard" in html
    assert "qd-v323-embedded-clipping-final-guard" in html
    assert ".app.embedded .main{grid-template-columns:minmax(300px,.44fr) minmax(0,1.56fr)" in html
    assert ".app.embedded .main{grid-template-columns:minmax(280px,520px) minmax(0,1fr)" in html
    assert ".app.embedded th:nth-child(n+8),.app.embedded td:nth-child(n+8){display:none}" in html
    assert ".app.embedded .chart-grid.time{grid-template-columns:minmax(0,1fr) minmax(188px,210px)" in html
    assert ".app.embedded .chart-grid.time{grid-template-columns:minmax(0,1fr) minmax(168px,188px)" in html
    assert "grid-template-areas:\"top\" \"main\" \"log\"" in html
    assert ".app.embedded .side{display:none}" in html
    assert "if(EMBEDDED_MODE)$('app').classList.add('embedded')" in html


def test_intraday_chart_uses_fixed_lunch_gap_and_clamps_tooltip():
    html = TestClient(api.app).get("/ui?symbol=300750&frame=time").text

    assert "function isCnLunchGap" in html
    assert "function isCnLunchMinutePoint" in html
    assert "function timeTradeFrac" in html
    assert "function timeTradeX" in html
    assert "function drawSegmentedTimeLine" in html
    assert "qd-v323-time-axis-final-guard" in html
    assert "function qdV323ClockMinuteFrac" in html
    assert "timeTradeFrac=qdV323ClockMinuteFrac" in html
    assert "午休断线" in html
    assert "breakLunch=true" in html
    assert "mode==='time'?true:breakLunch" in html
    assert "drawSegmentedTimeLine(ctx,data,d=>d.price,(d)=>timeTradeX(d,w),y,'#d1d5db',2,breakLunch)" in html
    assert "drawSegmentedTimeLine(ctx,data,d=>d.avg_price||d.price,(d)=>timeTradeX(d,w),y,'#f59e0b',2,breakLunch)" in html
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
