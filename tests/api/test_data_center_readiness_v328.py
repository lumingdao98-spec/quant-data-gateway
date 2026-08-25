from fastapi.testclient import TestClient

import quant_data.api as api


def test_decision_readiness_is_cache_only_and_keeps_missing_scores_missing(monkeypatch):
    def fake_framework(symbol: str, mode: str = "realtime_paper", strategy_family: str = "swing"):
        return {
            "ok": True,
            "data": {
                "name": "测试标的",
                "current_dimension_scores": {"technical": 61.0, "fundamental": None},
                "current_readiness": {
                    "strategy_family": strategy_family,
                    "auto_entry_eligible": False,
                    "entry_block_reasons": ["基本面快照缺失"],
                    "dimensions": [
                        {"key": "technical", "score": 61.0, "ready": True},
                        {
                            "key": "fundamental",
                            "score": None,
                            "ready": False,
                            "quality_status": "missing",
                            "missing_reasons": ["财报来源缺失"],
                        },
                    ],
                    "market_context": {},
                },
            },
        }

    monkeypatch.setattr(api, "decision_framework_symbol_v326", fake_framework)
    body = TestClient(api.app).get(
        "/api/data-center/decision-readiness?symbols=300750&mode=realtime_paper&strategy_family=swing"
    ).json()

    assert body["ok"] is True
    assert body["network_used"] is False
    assert body["data"][0]["scores"]["fundamental"] is None
    assert body["data"][0]["dimension_gate_eligible"] is False
    assert "基本面快照缺失" in body["data"][0]["entry_block_reasons"]


def test_information_refresh_reports_real_item_count_and_does_not_create_fallback(monkeypatch):
    monkeypatch.setattr(api.company_profile_service, "get_local_profile", lambda *args, **kwargs: {"name": "测试标的"})
    monkeypatch.setattr(
        api,
        "info_analyze",
        lambda *args, **kwargs: {
            "ok": True,
            "snapshot_id": "info-real-1",
            "cache_status": "refreshed",
            "data": {
                "items": [{"title": "可核验公告", "url": "https://example.com/announcement"}],
                "sources_status": [{"source": "官方公告", "count": 1, "status": "ok"}],
            },
        },
    )
    monkeypatch.setattr(
        api,
        "data_center_decision_readiness_v328",
        lambda **kwargs: {"ok": True, "data": [], "network_used": False},
    )

    body = TestClient(api.app).post(
        "/api/data-center/refresh",
        json={"symbols": ["300750"], "scopes": ["information"], "force": True},
    ).json()

    assert body["ok"] is True
    assert body["scopes"] == ["information"]
    assert body["results"][0]["ok"] is True
    assert body["results"][0]["data"]["item_count"] == 1
    assert body["results"][0]["data"]["snapshot_id"] == "info-real-1"


def test_information_refresh_keeps_missing_state_when_source_has_no_items(monkeypatch):
    monkeypatch.setattr(api.company_profile_service, "get_local_profile", lambda *args, **kwargs: {"name": "测试标的"})
    monkeypatch.setattr(
        api,
        "info_analyze",
        lambda *args, **kwargs: {"ok": True, "data": {"items": [], "sources_status": []}},
    )
    monkeypatch.setattr(
        api,
        "data_center_decision_readiness_v328",
        lambda **kwargs: {"ok": True, "data": [], "network_used": False},
    )

    body = TestClient(api.app).post(
        "/api/data-center/refresh",
        json={"symbols": ["300750"], "scopes": ["information"], "force": True},
    ).json()

    row = body["results"][0]
    assert body["partial"] is True
    assert row["ok"] is False
    assert row["data"]["item_count"] == 0
    assert "未取得可核验近期信息" in row["summary"]
