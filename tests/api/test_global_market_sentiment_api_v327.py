from fastapi.testclient import TestClient

import quant_data.api as api


def test_global_sentiment_api_preserves_session_and_correlation_metadata(monkeypatch):
    payload = {
        "score": 56.2,
        "label": "偏强",
        "valid_for_score": True,
        "correlation_family_units": 3,
        "selected_evidence": [{
            "key": "hang_seng_tech",
            "name": "恒生科技指数",
            "session_phase": "实时交易",
            "correlation_family": "greater_china_technology",
            "normalized_weight": 0.3,
            "source_ref": "https://finance.sina.com.cn/",
        }],
        "time_alignment_policy": "按交易时段区分实时、期货和前收盘",
        "correlation_policy": "相关资产族去重",
        "missing_reasons": [],
    }
    monkeypatch.setattr(
        api.global_market_sentiment_service,
        "snapshot",
        lambda **kwargs: payload,
    )

    response = TestClient(api.app).get("/api/market/global-sentiment?force=false")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["valid_for_score"] is True
    assert body["data"]["selected_evidence"][0]["session_phase"] == "实时交易"
    assert body["data"]["selected_evidence"][0]["correlation_family"] == "greater_china_technology"
