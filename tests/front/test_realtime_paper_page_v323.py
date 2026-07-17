from fastapi.testclient import TestClient

import quant_data.api as api


def test_realtime_paper_session_api_visible():
    data = TestClient(api.app).get("/api/backtest/v323/readiness").json()

    assert data["modules"]["realtime_paper"] is True


def test_realtime_paper_page_passes_strategy_parameters():
    html = TestClient(api.app).get("/realtime-paper").text

    assert "paperStrategyParamSummary" in html
    assert "selectedPaperStrategyParameters" in html
    assert "strategy_parameters:selectedPaperStrategyParameters(autoConfig)" in html
    assert "每策略参数已接入模拟" in html
    assert "max_drawdown_pct" in html
    assert "筛选 / 日K / 分时" in html
    assert "筛选底座 + 日K结构 + 分时择时" in html
    assert "include_orderbook=true" in html
    assert "买一 / 卖一" in html
    assert "scoreFromQuote" in html
    assert "intraday_score" in html
    assert "configApplyStatus" in html
    assert "已应用到当前会话" in html
    assert "reset_account:false" in html
    assert "AI 证据辅助" in html
    assert "/api/agent/market-brief" in html


def test_realtime_paper_page_has_visible_action_feedback_and_progressive_refresh():
    html = TestClient(api.app).get("/realtime-paper").text

    assert 'id="toast"' in html
    assert "withButton" in html
    assert "showToast" in html
    assert "Promise.allSettled" in html
    assert "条件已修改，正在保存" in html
    assert "配置已生效" in html
    assert "addEventListener('input',scheduleConfigApply)" in html
    assert "addEventListener('change',scheduleConfigApply)" in html
    assert "restoreAutoLoop" in html
    assert "已从服务端会话恢复自动循环" in html
