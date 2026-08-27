from fastapi.testclient import TestClient

import quant_data.api as api


def test_connected_market_agent_status_exposes_non_trading_multi_role_review():
    data = TestClient(api.app).get("/api/agent/status").json()

    assert data["multi_role_review"]["status"] == "ready"
    assert len(data["multi_role_review"]["roles"]) == 5
    assert data["multi_role_review"]["independent_risk_veto"] is True
    assert data["multi_role_review"]["order_capability"] is False


def test_connected_market_agent_brief_uses_real_stream_shape_and_safety(monkeypatch):
    def fake_stream(limit=80, force=False, live=True):
        return (
            {
                "items": [
                    {
                        "title": "金十快讯：美国非农数据公布前，美元指数震荡",
                        "source": "金十期货快讯",
                        "published_at": "2026-07-04 08:00:00",
                        "source_ref": "https://qihuo.jin10.com/",
                        "impact_scope": "宏观/美元/商品",
                        "message_dimension": "国际消息/全球市场",
                        "impact_targets": ["成长股估值", "美元指数", "美债收益率"],
                        "affected_sectors": ["成长股估值"],
                        "affected_assets": ["美元指数", "美债收益率"],
                        "impact_note": "非农和利率预期可能影响成长股估值与市场风险偏好。",
                    },
                    {
                        "title": "宁德时代发布储能系统新品并获得海外订单",
                        "source": "交易所公告",
                        "published_at": "2026-07-04 08:02:00",
                        "source_ref": "https://example.com/300750-announcement",
                        "impact_targets": ["储能系统", "动力电池"],
                        "affected_sectors": ["储能系统"],
                        "impact_note": "公司和产业链直接命中。",
                    },
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
    assert brief["global_flash_count"] == 2
    assert brief["source_link_count"] >= 1
    assert brief["recommended_action"] == "paper_then_precheck"
    impacts = brief["symbol_global_impacts"]
    assert impacts[0]["symbol"] == "300750"
    assert impacts[0]["related_events"]
    assert impacts[0]["related_events"][0]["source_ref"] == "https://example.com/300750-announcement"
    assert "储能系统" in impacts[0]["related_events"][0]["matched_terms"]
    assert impacts[0]["market_context_events"][0]["source_ref"] == "https://qihuo.jin10.com/"
    assert impacts[0]["market_context_events"][0]["score_included"] is False
    assert brief["symbol_decisions"][0]["action"] == "模拟验证/实盘预检查"
    assert "LIVE_TRADING_ENABLED=false" in "；".join(brief["risk_flags"])
    assert "不能直接下单" in brief["llm_status"]
    assert "不构成投资建议" in brief["disclaimer"]
    review = brief["multi_role_review"]
    assert review["review_id"].startswith("MRR-")
    assert len(review["roles"]) == 5
    assert review["debate"]["bull_case"]
    assert review["risk_committee"]["verdict"] == "blocked"
    assert review["portfolio_committee"]["order_capability"] is False
    assert review["checkpoint"]["persisted"] is False


def test_connected_market_agent_exposes_traceable_theme_trends(monkeypatch):
    monkeypatch.setattr(api, "_read_global_news_stream", lambda limit=80, force=False, live=True: ({"items": []}, {"status": "miss"}))
    monkeypatch.setattr(api.score_history_service, "latest", lambda limit=1000, score_date=None: [])
    monkeypatch.setattr(
        api.sector_mainline_service,
        "snapshot",
        lambda **kwargs: {
            "ok": True,
            "items": [
                {
                    "board_code": "BK1036",
                    "board_name": "半导体",
                    "board_type_name": "行业板块",
                    "stage": "强势",
                    "mainline_score": 78.5,
                    "strength_score": 81.0,
                    "net_inflow": 1_260_000_000,
                    "interval_flow_15m": 160_000_000,
                    "interval_flow_30m": 280_000_000,
                    "interval_flow_60m": 410_000_000,
                    "recent_flow_5d_sum": 3_080_000_000,
                    "flow_state": "加速流入",
                    "flow_state_reason": "近15和30分钟累计净流均为正",
                    "published_at": "2026-07-20T10:30:00",
                    "source_name": "东方财富公开板块资金",
                    "source_ref": "https://push2.eastmoney.com/api/qt/clist/get",
                    "source_url": "https://data.eastmoney.com/bkzj/",
                },
                {
                    "board_code": "BK0000",
                    "board_name": "样本不足板块",
                    "stage": "观察",
                    "mainline_score": 66,
                    "flow_state": "等待日内快照",
                    "source_name": "",
                    "source_ref": "",
                },
            ],
        },
    )
    monkeypatch.setattr(
        api.live_trading_engine_v323,
        "status",
        lambda: {
            "broker": {"connected": False, "status": "disabled"},
            "safety": {"LIVE_TRADING_ENABLED": False, "ORDER_CONFIRM_REQUIRED": True, "LIVE_KILL_SWITCH": False},
        },
    )

    brief = TestClient(api.app).get("/api/agent/market-brief?symbols=300750").json()["data"]

    trends = {row["theme"]: row for row in brief["theme_trends"]}
    semiconductor = trends["半导体"]
    assert semiconductor["trend"] == "增强"
    assert semiconductor["support_evidence"]
    assert semiconductor["source_ref"].startswith("https://push2.eastmoney.com/")
    assert semiconductor["truth_boundary"].startswith("板块资金为公开累计净流字段")
    missing = trends["样本不足板块"]
    assert missing["trend"] == "等待数据"
    assert "缺少可追溯板块资金来源" in missing["missing_data"]
    assert brief["ai_analysis"]["status"] == "not_requested"
