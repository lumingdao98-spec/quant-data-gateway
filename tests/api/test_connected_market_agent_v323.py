from fastapi.testclient import TestClient

import quant_data.api as api


def test_connected_market_agent_brief_uses_real_stream_shape_and_safety(monkeypatch):
    def fake_stream(limit=80, force=False, live=True):
        return (
            {
                "items": [
                    {
                        "title": "金十快讯：美国非农数据公布前，美元指数震荡",
                        "source": "金十期货快讯",
                        "published_at": "2026-07-04 08:00:00",
                        "impact_scope": "宏观/美元/商品",
                        "message_dimension": "国际消息/全球市场",
                    }
                ],
                "stream_mode": "test_live_fetch",
                "sources_status": [{"source": "金十期货快讯", "count": 1, "status": "ok"}],
            },
            {"status": "test_no_write", "stale": False},
        )

    monkeypatch.setattr(api, "_read_global_news_stream", fake_stream)
    monkeypatch.setattr(
        api.score_history_service,
        "latest",
        lambda limit=1000, score_date=None: [
            {"symbol": "300750", "name": "宁德时代", "total_score": 72.5, "updated_at": "2026-07-04 08:01:00"},
            {"symbol": "600438", "name": "通威股份", "total_score": 51.0, "updated_at": "2026-07-04 08:01:00"},
        ],
    )
    monkeypatch.setattr(
        api.live_trading_engine_v323,
        "status",
        lambda: {
            "broker": {"connected": False, "status": "disabled"},
            "safety": {"LIVE_TRADING_ENABLED": False, "ORDER_CONFIRM_REQUIRED": True, "LIVE_KILL_SWITCH": False},
        },
    )

    data = TestClient(api.app).get("/api/agent/market-brief?symbols=300750,600438&limit=20").json()

    assert data["ok"] is True
    brief = data["data"]
    assert brief["agent_id"] == "connected_market_agent_v323"
    assert brief["mode"] == "evidence_only_online_agent"
    assert brief["global_flash_count"] == 1
    assert brief["recommended_action"] == "paper_then_precheck"
    assert brief["symbol_decisions"][0]["action"] == "模拟验证/实盘预检查"
    assert "LIVE_TRADING_ENABLED=false" in "；".join(brief["risk_flags"])
    assert "未接入外部 LLM 下单" in brief["llm_status"]
    assert "不构成投资建议" in brief["disclaimer"]
