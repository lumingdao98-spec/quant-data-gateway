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


def test_global_sentiment_api_passes_symbol_profile_and_explicit_sector(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        api.company_profile_service,
        "get_profile",
        lambda symbol, **kwargs: {"symbol": symbol, "industry": "光伏设备", "business_tags": ["硅片"]},
    )

    def snapshot(**kwargs):
        captured.update(kwargs)
        return {"focus_label": "光伏与太阳能", "valid_for_score": False, "missing_reasons": []}

    monkeypatch.setattr(api.global_market_sentiment_service, "snapshot", snapshot)

    response = TestClient(api.app).get(
        "/api/market/global-sentiment?symbol=600438&industry=光伏&themes=硅料"
    )

    assert response.status_code == 200
    assert captured["symbol"] == "600438"
    assert captured["profile"]["industry"] == "光伏设备"
    assert captured["focus_terms"] == ["光伏", "硅料"]


def test_capital_evidence_api_exposes_truth_boundaries(monkeypatch):
    monkeypatch.setattr(
        api.individual_capital_evidence_service,
        "snapshot",
        lambda symbol, **kwargs: {
            "symbol": symbol,
            "score": 57.5,
            "quality_status": "partial",
            "public_daily_flow": {"available": True},
            "intraday_proxy": {"available": True},
            "institutional_holdings": {"available": True, "report_date": "2026-06-30"},
            "truth_boundary": "不是Level-2主力账户证明。",
        },
    )
    monkeypatch.setattr(
        api.company_profile_service,
        "get_local_profile",
        lambda symbol, **kwargs: {"name": "宁德时代", "industry": "动力电池"},
    )

    response = TestClient(api.app).get(
        "/api/market/capital-evidence/300750?force=false&allow_network=false"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["score"] == 57.5
    assert body["data"]["name"] == "宁德时代"
    assert body["data"]["institutional_holdings"]["report_date"] == "2026-06-30"
    assert "不代表实时主力账户" in body["disclaimer"]
