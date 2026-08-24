from fastapi.testclient import TestClient

import quant_data.api as api


def test_auto_trading_workbench_explains_session_aware_global_market_context():
    html = TestClient(api.app).get("/auto-trading").text

    assert "全球科技时段情绪" in html
    assert "/api/market/global-sentiment" in html
    assert "按各市场开盘时间分别判断" in html
    assert "权重上限15%" in html
    assert "相关性去重" in html
    assert ".sector-link{color:#67e8f9!important" in html
    assert "refreshed:'已刷新'" in html


def test_live_trading_page_has_read_only_multisymbol_decision_board():
    html = TestClient(api.app).get("/live-trading").text

    assert "实盘决策观察（只读）" in html
    assert "买一" in html
    assert "卖一" in html
    assert "持仓" in html
    assert "成本" in html
    assert "浮盈亏" in html
    assert "/api/quotes?symbols=" in html
    assert "/api/score/latest/" in html
    assert "不会触发评分重算或下单" in html
    assert "frame=1d&embedded=1" in html
    assert "资金和盈亏不显示占位零值" in html
    assert "label(broker)" in html


def test_backtest_defaults_to_compact_markers_and_declares_pit_boundary():
    html = TestClient(api.app).get("/backtest?symbol=300750").text

    assert "异常：近7日/严重" in html
    assert "异常：全部（每日最多4个）" in html
    assert "showTradeMarkers" in html
    assert "showAllAnomalies" in html
    assert "实时行情绝不回填到历史日期" in html
    assert "visibleAnomalies" in html


def test_detail_chart_clusters_duplicate_markers_without_dropping_audit_rows():
    html = TestClient(api.app).get("/ui?symbol=300750&frame=1d").text

    assert "qd-v327-marker-cluster" in html
    assert "function compactChartMarkers" in html
    assert "function chartMarkersForRows" in html
    assert "function markerAnchorPrice" in html
    assert "raw>=lo*.85&&raw<=hi*1.15" in html
    assert "visibleMarkerPrices=function(){return[]}" in html
    assert "byDate[date].slice(0,4)" in html
    assert "已合并重复" in html
    assert "collectAllMarkers()" in html
    assert "qd-v327-chart-density" in html
    assert "缓存${cnCacheStatus(state)}" in html
