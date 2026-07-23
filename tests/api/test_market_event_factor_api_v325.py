from fastapi.testclient import TestClient

import quant_data.api as api


def test_market_event_factor_api_separates_market_and_symbol_scope(monkeypatch):
    monkeypatch.setattr(
        api.company_profile_service,
        "get_profile",
        lambda symbol, force=False, local_only=False: {"symbol": symbol, "name": "测试公司", "industry": "测试行业"},
    )
    monkeypatch.setattr(
        api.realtime_decision_service.market_event_factors,
        "build_context",
        lambda **kwargs: {
            "symbol": kwargs["symbol"],
            "market_adjustment": -7,
            "information_adjustment": 0,
            "factors": [{"scope": "市场环境", "factor_name_cn": "全球科技风险", "adjustment": -7}],
            "truth_boundary": "仅作事件解释",
        },
    )

    response = TestClient(api.app).get("/api/market/event-factors/300750")
    body = response.json()

    assert response.status_code == 200
    assert body["ok"] is True
    assert body["data"]["market_adjustment"] == -7
    assert body["data"]["information_adjustment"] == 0
    assert body["data"]["factors"][0]["scope"] == "市场环境"
