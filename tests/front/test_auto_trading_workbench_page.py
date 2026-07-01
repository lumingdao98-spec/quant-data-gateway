from fastapi.testclient import TestClient

import quant_data.api as api


def test_auto_trading_workbench_page_visible():
    html = TestClient(api.app).get("/auto-trading").text

    assert "自动交易总控台" in html
    assert "当前推荐路径" in html
    assert "新手交易路径" in html
    assert "strategySelectedSummary" in html
    assert "renderStrategySelectionSummary" in html
    assert "QMT / PTrade" in html
    assert "paperControl" in html
    assert "quick-flow" in html
    assert "quick-step" in html
    assert "embeddedWorkspace" in html
    assert "workspaceFrame" in html
    assert "workspaceTabs" in html
    assert "openWorkspaceModule" in html
    assert "reloadWorkspaceFrame" in html
    assert "openWorkspaceInNewWindow" in html
    assert 'src="/screener"' in html
    assert "data-url=\"/ui?symbol=300750&frame=time\"" in html
    assert "data-url=\"/detail/300750?frame=1d\"" in html
    assert "data-url=\"/backtest?symbol=300750\"" in html
    assert "data-url=\"/realtime-paper\"" in html
    assert "data-url=\"/live-trading\"" in html
    assert "data-url=\"/trading-records\"" in html
    assert "data-url=\"/data-center\"" in html
    assert "presetRow" in html
    assert "strategyCatalog" in html
    assert "selectBeginnerPreset" in html
    assert "toggleStrategyFromCatalog" in html
    assert "quote_hydrate_request" in html
    assert "/api/live-broker/status" in html
    assert "/api/auto-trading/config" in html
    assert "/api/auto-trading/config/one-click" in html
    assert "/api/auto-trading/start-paper" in html
    assert "/api/realtime-paper/sessions/" in html
    assert "/api/data-center/status" in html
    assert "strategyCombo" in html
    assert "strategyParamJson" in html
    assert "strategyParamRows" in html
    assert "renderStrategyParamEditor" in html
    assert "collectStrategyParamEditor" in html
    assert "dimensionStrip" in html
    assert "renderScoreDimensions" in html
    assert "positionSizing" in html
    assert "resetAccount" in html
    assert "reset_account" in html
    assert "maxDrawdownPct" in html
    assert "runConfigBacktest" in html
    assert "technical_score:68" not in html
    assert "fundamental_score:60" not in html


def test_chinese_docs_include_auto_trading_v323_entrypoints():
    html = TestClient(api.app).get("/docs-cn").text

    assert "/auto-trading" in html
    assert "/api/auto-trading/config" in html
    assert "/api/auto-trading/config/one-click" in html
    assert "/api/auto-trading/start-paper" in html
