from fastapi.testclient import TestClient

import quant_data.api as api


def test_auto_trading_one_click_config_and_start_paper():
    client = TestClient(api.app)
    payload = {
        "symbols": "300750，600438;510300",
        "strategy_family": "hybrid",
        "strategy_combo": ["score_driven", "ma_repair", "event_driven", "risk_control"],
        "position_sizing": "atr_risk",
        "interval_seconds": 15,
        "initial_cash": 120000,
        "risk_controls": {
            "stop_loss_pct": 7,
            "take_profit_pct": 16,
            "max_drawdown_pct": 12,
            "max_single_position_pct": 18,
            "max_total_position_pct": 70,
            "min_cash_pct": 20,
        },
        "event_watch": {
            "financial_reports": True,
            "half_year_reports": True,
            "exchange_announcements": True,
            "major_negative_news": True,
            "policy_industry_news": True,
        },
    }

    configured = client.post("/api/auto-trading/config/one-click", json=payload).json()

    assert configured["ok"] is True
    assert configured["data"]["symbols"] == ["300750", "600438", "510300"]
    assert configured["data"]["strategy_combo"] == ["score_driven", "ma_repair", "event_driven", "risk_control"]
    assert configured["data"]["position_sizing"] == "atr_risk"
    assert configured["data"]["risk_controls"]["stop_loss_pct"] == 7.0
    assert configured["data"]["risk_controls"]["max_drawdown_pct"] == 12.0
    assert configured["data"]["event_watch"]["half_year_reports"] is True
    assert configured["readiness"]["ready_for_paper"] is True

    started = client.post("/api/auto-trading/start-paper", json=payload).json()

    assert started["ok"] is True
    assert started["session"]["status"] == "running"
    assert started["config"]["symbols"] == ["300750", "600438", "510300"]
    assert started["config"]["strategy_combo"] == ["score_driven", "ma_repair", "event_driven", "risk_control"]
    assert started["readiness"]["ready_for_paper"] is True
