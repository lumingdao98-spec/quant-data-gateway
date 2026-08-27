from fastapi.testclient import TestClient

import quant_data.api as api


def test_auto_trading_workbench_page_visible():
    html = TestClient(api.app).get("/auto-trading").text

    assert "V3.28 自动交易总控台" in html
    assert "首页总览 + 右侧覆盖模块" in html
    assert "交易工作流" in html
    assert "联网智能辅助" in html
    assert "多角色证据复核" in html
    assert "主线板块 · 日内资金轮动与近期强度" in html
    assert "近15分" in html
    assert "近5分钟" in html
    assert "近60分" in html
    assert "setSectorWindow" in html
    assert "近5日净流" in html
    assert "资金回流" in html
    assert "/api/market/sectors/mainline" in html
    assert "公开资金净流" in html
    assert "宏观事件" not in html or "/api/macro/global-events" in html
    assert "paperControl" in html
    assert "strategySelectedSummary" in html
    assert "strategyCatalog" in html
    assert "strategyParamRows" in html
    assert "collectStrategyParamEditor" in html
    assert "maxDrawdownPct" in html
    assert "reset_account" in html
    assert "强制新建模拟账户（清空当前持仓与成交）" in html
    assert "已恢复当前模拟账户" in html
    assert "runConfigBacktest" in html
    assert "quote_hydrate_request" in html
    assert "/api/live-broker/status" in html
    assert "/api/live-broker/setup" in html
    assert "/api/live-broker/setup/validate" in html
    assert "券商接入向导" in html
    assert "同花顺 / SuperMind 授权桥" in html
    assert "普通同花顺客户端只做行情查看" in html
    assert "/api/notifications/mobile/status" in html
    assert "/api/notifications/mobile/preview" in html
    assert "/api/notifications/mobile/test" in html
    assert "移动端交易提醒" in html
    assert "只读校验" in html
    assert "网页输入未写入" in html or "不写入磁盘" in html
    assert "renderBrokerSetup" in html
    assert "/api/integrations/tonghuashun/status" in html
    assert "同花顺委托提醒" in html
    assert "不会自动点击下单" in html
    assert "/api/auto-trading/config" in html
    assert "/api/auto-trading/config/one-click" in html
    assert "/api/auto-trading/start-paper" in html
    assert "/api/agent/market-brief" in html
    assert "/api/realtime-paper/sessions/" in html
    assert "/api/data-center/status" in html
    assert "/api/macro/global-events" in html
    assert "/api/news/global/stream" in html
    assert "/api/agent/market-brief" in html
    assert "globalTicker" in html
    assert "globalStream" in html
    assert "globalStreamSources" in html
    assert "sourceUrlOf" in html
    assert "sourceLabelOf" in html
    assert "sourceMetaHtml" in html
    assert "sourceLinksHtml" in html
    assert "impactTagsOf" in html
    assert "impactNoteOf" in html
    assert "eventStatusHtml" in html
    assert "早期线索" in html
    assert "交易用途" in html
    assert "decision_scope_cn" in html
    assert "decision_use_cn" in html
    assert "已合并 ${merged} 条同事件信息" in html
    assert "renderGlobalFeed" in html
    assert "renderGlobalStreamSources" in html
    assert "source-link" in html
    assert "source-link-row" in html
    assert "source-meta" in html
    assert "source-policy" in html
    assert "impact-tag" in html
    assert "impact-summary" in html
    assert "symbol-impact-card" in html
    assert "查看来源 / 原文" in html
    assert "来源：${esc(sourceLabelOf(x))}" in html
    assert "impactTagsOf(x)" in html
    assert "globalStreamRefreshMs" in html
    assert "loadGlobalStream" in html
    assert "portfolioOverview" in html
    assert "recordOverviewRows" in html
    assert "renderPortfolioOverview" in html
    assert "当前模拟账户" in html
    assert "持仓成本" in html
    assert "总成交额" in html
    assert "latestPaperPortfolio" in html
    assert "/api/live/account" in html
    assert "/api/live/positions" in html
    assert "/api/live/orders/preview-batch" in html
    assert "股票池批量预检查" in html
    assert "livePreviewSummary" in html
    assert "agentDecision" in html
    assert "renderAgentDecision" in html
    assert "multi_role_review" in html
    assert "展开五角色观点、正反辩论与复盘检查点" in html
    assert "风险委员会" in html
    assert "symbol_global_impacts" in html
    assert "source_link_count" in html
    assert "个股影响映射" in html
    assert "暂无全球快讯直接命中" in html
    assert "查看影响来源 / 原文" in html
    assert "agent-evidence-list" in html
    assert "agent-evidence" in html
    assert "打开来源 / 原文" in html
    assert "impactNoteOf(x)" in html
    assert "startGlobalStreamLoop" in html
    assert "暂停轮播" in html
    assert 'id="actionToast"' in html
    assert "showActionToast" in html
    assert "Promise.allSettled" in html
    assert "核心状态已更新" in html
    assert "总控台已更新" in html
    assert "这个分数怎么来的" in html
    assert "默认执行分目标权重" in html
    assert "资金面" in html
    assert 'id="flowScore"' in html
    assert "scoreFreshness.status" in html
    assert "缺失项不补 50 分" in html
    assert "未参与" in html
    assert "scoreFrom" in html
    assert "scoreExplain" in html
    assert "renderScoreExplain" in html
    assert "基本/技术/信息/资金、大盘与自动入场门禁" in html
    assert "真实性/新鲜度门禁剔除" in html
    assert "dimensionReadiness" in html
    assert "renderDimensionReadiness" in html
    assert "/api/decision-framework/" in html
    assert "只作审计对照，不与分项重复计票" in html
    assert "/api/market/event-factors/" in html
    assert "市场事件调整" in html
    assert "event-factor-list" in html
    assert "复核全部持仓" in html
    assert "只读持仓复核" in html
    assert "/position-reviews?limit=50" in html
    assert "/review-positions" in html
    assert "renderPositionReviews" in html
    assert "高级自定义（完整策略目录与逐项参数）" in html
    assert "按股票池推荐" in html
    assert "波段观察" in html
    assert "affected_companies" in html
    assert "证券代码" in html
    assert "暂无直接映射" in html
    assert "首页只保留快速配置" in html
    assert "展开完整配置与逐项参数" in html
    assert ".hero>.panel:nth-child(2)>.panel-b{max-height:248px" in html
    assert ".grid-main{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))" in html
    assert ".grid-main>.stack{display:grid;gap:14px;align-content:start" in html
    assert ".grid-main>.stack{display:contents}" in html
    assert 'id="homeScorePanel"' in html
    assert 'class="home-score-layout"' in html
    assert 'id="homeStatusPanel"' in html
    assert 'id="homePaperPanel"' in html
    assert 'id="homePortfolioPanel"' in html
    assert "#homeScorePanel{grid-column:1/-1;grid-row:1}" in html
    assert "function arrangeDashboardPanels" in html
    assert "layoutKey==='medium'?[[3,0,6],[4,1,2,5,7]]" in html
    assert "dashboard-fold" in html
    assert "展开自动复评、持仓复核和会话计数" in html
    assert "展开券商预检查、同花顺提醒和持仓复核" in html
    assert ".sector-table-wrap{overflow:auto;max-width:100%;max-height:280px" in html


def test_auto_trading_workbench_uses_single_right_overlay_iframe():
    html = TestClient(api.app).get("/auto-trading").text

    assert "iframe-shell" in html
    assert "width:calc(100vw - 228px)" in html
    assert 'id="workspaceFrame"' in html
    assert html.count('class="workspace-frame"') == 1
    assert "addEventListener('load',handleWorkspaceFrameLoad)" in html
    assert "function embeddedModuleUrl" in html
    assert "function moduleKeyFromUrl" in html
    assert "if(parsed.pathname==='/auto-trading')" in html


def test_every_workbench_module_uses_embedded_shell():
    client = TestClient(api.app)
    workbench = client.get("/auto-trading").text

    for path in (
        "/screener?embedded=1",
        "/realtime-paper?embedded=1",
        "/live-trading?embedded=1",
        "/broker-setup?embedded=1",
        "/trading-records?embedded=1",
        "/data-center?embedded=1",
        "/docs-cn?embedded=1",
    ):
        assert path in workbench

    for path in (
        "/screener?embedded=1",
        "/backtest?embedded=1",
        "/realtime-paper?embedded=1",
        "/live-trading?embedded=1",
        "/broker-setup?embedded=1",
        "/trading-records?embedded=1",
        "/data-center?embedded=1",
        "/info?embedded=1",
        "/docs-cn?embedded=1",
    ):
        html = client.get(path).text
        assert "qd-v328-embedded-module-shell" in html
        assert "qd-embedded-module" in html
        assert 'a[href="/auto-trading"]{display:none!important}' in html


def test_embedded_realtime_keeps_three_readable_columns_in_workbench():
    html = TestClient(api.app).get("/realtime-paper?embedded=1").text

    assert "grid-template-columns:240px minmax(0,1fr) 260px!important" in html
    assert "@media(max-width:960px)" in html
    assert 'grid-template-areas:"side" "main" "right" "log"' in html


def test_workbench_shows_exact_score_snapshot_freshness_and_fundamental_gate():
    html = TestClient(api.app).get("/auto-trading").text

    assert "评分时效" in html
    assert "snapshot_note" in html
    assert "dm.fundamental?.ready" in html
    assert 'src="about:blank"' in html
    assert "openModule(" in html
    assert "closeWorkspace" in html
    assert "frame.src='about:blank'" in html
    assert "currentModule && currentModule!==key" in html
    assert "/ui?symbol=" in html
    assert "frame=time&embedded=1" in html
    assert "frame=1d&embedded=1" in html
    assert "!/[?&]embedded=1\\b/.test(url)" in html
    assert "/detail/" in html
    assert "/backtest?symbol=" in html
    assert "/realtime-paper" in html
    assert "/live-trading" in html
    assert "/trading-records" in html
    assert "/data-center" in html


def test_auto_trading_workbench_lazily_hydrates_advanced_strategy_editor():
    html = TestClient(api.app).get("/auto-trading").text

    assert 'id="strategyAdvancedDetails"' in html
    assert 'ontoggle="onStrategyEditorToggle(this)"' in html
    assert "let strategyEditorHydrated=false" in html
    assert "let deferredStrategyConfig=null" in html
    assert "if(!strategyEditorHydrated&&!strategyEditorIsOpen())return" in html
    assert "const existing=cfg.strategy_parameters||{}" in html
    assert "展开高级自定义后加载完整策略目录" in html
    assert "展开高级自定义后加载逐项参数" in html
    assert "renderGlobalFeed(macro);renderAgentDecision(agent)" in html
    assert "renderGlobalFeed(macro);renderGlobalStream(stream)" not in html
    assert html.count("api('/api/news/global/stream?") == 1
    assert "api('/api/news/jin10/realtime?" not in html


def test_auto_trading_workbench_prefers_aggregated_paper_session_overview():
    html = TestClient(api.app).get("/auto-trading").text

    assert "async function loadSessionOverview(base)" in html
    assert "base+'/overview?orders_limit=500&fills_limit=500&markers_limit=50&audit_limit=100&reviews_limit=50'" in html
    assert "if(overview?.ok&&overview.data)return overview.data" in html
    assert "realtime paper overview fallback" in html
    assert "const {snapshot,orders,fills,positions,markers,audit,reviews}=await loadSessionOverview(base)" in html
    assert "api(base+'/position-reviews?limit=50')" in html


def test_auto_trading_workbench_prefers_aggregated_dashboard_overview():
    html = TestClient(api.app).get("/auto-trading").text

    assert "async function loadDashboardCoreOverview()" in html
    assert "api('/api/auto-trading/dashboard-overview?records_limit=30')" in html
    assert "if(overview?.ok&&overview.data)" in html
    assert "auto trading dashboard overview fallback" in html
    assert "const core=await loadDashboardCoreOverview()" in html
    assert "api('/api/live-broker/status')" in html
    assert "api('/api/realtime-paper/scheduler/status')" in html


def test_embedded_quote_page_has_workbench_layout_guards():
    html = TestClient(api.app).get("/ui?symbol=300750&frame=time&embedded=1").text

    assert "qd-v323-workbench-iframe-layout" in html
    assert ".app.embedded .main" in html
    assert "display:flex!important" in html
    assert "flex-direction:column!important" in html
    assert "max-height:260px!important" in html
    assert ".app.embedded .detail" in html
    assert "min-height:780px!important" in html
    assert ".app.embedded .chart-grid.time" in html
    assert "grid-template-columns:minmax(0,1fr) minmax(176px,212px)!important" in html
    assert ".app.embedded .book" in html
    assert "max-width:212px!important" in html
    assert ".app.embedded .tooltip" in html
    assert "calc(100vw - 28px)" in html


def test_root_redirects_to_auto_trading():
    response = TestClient(api.app).get("/", follow_redirects=False)

    assert response.status_code in {307, 308}
    assert response.headers["location"] == "/auto-trading"


def test_chinese_docs_include_auto_trading_v323_entrypoints():
    html = TestClient(api.app).get("/docs-cn").text

    assert "/auto-trading" in html
    assert "/api/auto-trading/config" in html
    assert "/api/auto-trading/config/one-click" in html
    assert "/api/auto-trading/start-paper" in html
    assert "/api/agent/market-brief" in html
