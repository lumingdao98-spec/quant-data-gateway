from fastapi.testclient import TestClient

import quant_data.api as api


def test_auto_trading_workbench_page_visible():
    html = TestClient(api.app).get("/auto-trading").text

    assert "自动交易总控台" in html
    assert "首页总览 + 右侧覆盖模块" in html
    assert "交易工作流" in html
    assert "联网智能辅助" in html
    assert "宏观事件" not in html or "/api/macro/global-events" in html
    assert "paperControl" in html
    assert "strategySelectedSummary" in html
    assert "strategyCatalog" in html
    assert "strategyParamRows" in html
    assert "collectStrategyParamEditor" in html
    assert "maxDrawdownPct" in html
    assert "reset_account" in html
    assert "runConfigBacktest" in html
    assert "quote_hydrate_request" in html
    assert "/api/live-broker/status" in html
    assert "/api/auto-trading/config" in html
    assert "/api/auto-trading/config/one-click" in html
    assert "/api/auto-trading/start-paper" in html
    assert "/api/agent/market-brief" in html
    assert "/api/realtime-paper/sessions/" in html
    assert "/api/data-center/status" in html
    assert "/api/macro/global-events" in html
    assert "/api/news/global/stream" in html
    assert "/api/news/jin10/realtime" in html
    assert "/api/agent/market-brief" in html
    assert "globalTicker" in html
    assert "globalStream" in html
    assert "globalStreamSources" in html
    assert "mergeGlobalStreams" in html
    assert "sourceUrlOf" in html
    assert "impactTagsOf" in html
    assert "impactNoteOf" in html
    assert "source-link" in html
    assert "impact-tag" in html
    assert "globalStreamRefreshMs" in html
    assert "loadGlobalStream" in html
    assert "agentDecision" in html
    assert "renderAgentDecision" in html
    assert "startGlobalStreamLoop" in html
    assert "暂停轮播" in html


def test_auto_trading_workbench_uses_single_right_overlay_iframe():
    html = TestClient(api.app).get("/auto-trading").text

    assert "iframe-shell" in html
    assert 'id="workspaceFrame"' in html
    assert html.count('class="workspace-frame"') == 1
    assert 'src="about:blank"' in html
    assert "openModule(" in html
    assert "closeWorkspace" in html
    assert "frame.src='about:blank'" in html
    assert "currentModule && currentModule!==key" in html
    assert "/ui?symbol=" in html
    assert "frame=time&embedded=1" in html
    assert "frame=1d&embedded=1" in html
    assert "/detail/" in html
    assert "/backtest?symbol=" in html
    assert "/realtime-paper" in html
    assert "/live-trading" in html
    assert "/trading-records" in html
    assert "/data-center" in html


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
