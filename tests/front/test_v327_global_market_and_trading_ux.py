from fastapi.testclient import TestClient

import quant_data.api as api


def test_auto_trading_workbench_explains_session_aware_global_market_context():
    html = TestClient(api.app).get("/auto-trading").text

    assert "所选板块的全球参照" in html
    assert "/api/market/global-sentiment" in html
    assert "按行业选择海外基准" in html
    assert "symbol='+encodeURIComponent(primarySymbol())" in html
    assert "行业基准" in html
    assert "应用参照" in html
    assert "映射依据" in html
    assert "权重上限15%" in html
    assert "相关性去重" in html
    assert ".sector-link{color:#67e8f9!important" in html
    assert "refreshed:'已刷新'" in html
    assert "个股资金流与机构持仓披露" in html
    assert "/api/market/capital-evidence/" in html
    assert "5/15/30/60" in html
    assert "公开主力净流占比" in html
    assert "当日分时量价方向代理" in html
    assert "不等于逐笔主动买卖" in html
    assert "liveAccount?.data_available===true" in html
    assert "可用资金 --；总资产 --；持仓 --；浮盈亏 --" in html
    assert "--（券商未连接或未授权）" in html
    assert "当前缓存只读评估（不生成订单）" in html
    assert "最近一次落库决策快照" in html
    assert "不代表上方当前只读评估仍然缺失" in html
    assert "fundamental:'基本面'" in html
    assert "market:'大盘情绪'" in html
    assert ".capital-window b{font-size:10px!important" in html
    assert "全球行业走势参照" in html
    assert 'id="globalScoreContribution"' in html
    assert "let globalMarketRequestSeq=0" in html
    assert "focusOverride===null" in html
    assert "requestSeq===globalMarketRequestSeq" in html
    assert "loadGlobalMarketSentiment(false,btn,nextFocus)" in html
    assert "手工选择只改变本观察面板" in html
    assert "当前个股评分与风险" in html
    assert "===primarySymbol())||null" in html
    assert 'id="globalSectorReferenceToggle"' in html
    assert "function toggleGlobalReferenceStrategy(enabled)" in html
    assert "不能单独触发买入" in html
    assert "旧版极简组合已在编辑器中补全为推荐策略" in html
    assert "保存配置”或“启动模拟”后才会成为运行配置" in html


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
    assert "byDate[date].slice(0,3)" in html
    assert "已合并重复" in html
    assert "collectAllMarkers()" in html
    assert "qd-v327-chart-density" in html
    assert "缓存${cnCacheStatus(state)}" in html
