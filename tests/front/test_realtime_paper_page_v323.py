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
