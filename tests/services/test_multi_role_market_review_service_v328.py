from quant_data.services.multi_role_market_review_service import MultiRoleMarketReviewService


def _build_review():
    service = MultiRoleMarketReviewService()
    return service.build(
        symbols=["300750", "600438"],
        decisions=[
            {"symbol": "300750", "name": "宁德时代", "score": 72.5, "action": "模拟验证", "score_time": "2026-08-27T10:00:00"},
            {"symbol": "600438", "name": "通威股份", "score": 51.0, "action": "观察", "score_time": "2026-08-27T10:00:00"},
        ],
        score_rows={
            "300750": {"snapshot": {"fundamental_score": 68.0}},
            "600438": {},
        },
        evidence=[
            {
                "title": "储能产业政策发布",
                "source": "交易所公告",
                "source_ref": "https://example.com/announcement",
                "published_at": "2026-08-27T09:00:00",
            }
        ],
        symbol_impacts=[
            {"symbol": "300750", "name": "宁德时代", "related_events": [{"title": "储能产业政策发布"}]},
            {"symbol": "600438", "name": "通威股份", "related_events": []},
        ],
        theme_trends=[
            {
                "theme": "新能源",
                "trend": "增强",
                "support_evidence": ["近15分钟公开净流为正"],
                "counter_evidence": [],
                "missing_data": [],
                "source_ref": "https://example.com/sector-flow",
                "published_at": "2026-08-27T10:00:00",
            }
        ],
        macro_watchlist=[
            {
                "label": "美国 CPI/PCE 通胀",
                "evidence_count": 1,
                "latest_title": "美国通胀数据发布",
                "latest_source_ref": "https://example.com/cpi",
            }
        ],
        risk_flags=["LIVE_TRADING_ENABLED=false，当前只能模拟/预检查"],
        safety={"LIVE_TRADING_ENABLED": False, "ORDER_CONFIRM_REQUIRED": True, "LIVE_KILL_SWITCH": False},
        broker_connected=False,
        recommended_action="paper_then_precheck",
    )


def test_multi_role_review_separates_roles_debate_and_risk_veto():
    review = _build_review()

    assert review["version"] == "v3.28-multi-role-evidence-review"
    assert {row["role"] for row in review["roles"]} == {
        "technical_score",
        "fundamental",
        "information",
        "capital_flow",
        "market_macro",
    }
    assert review["debate"]["bull_case"]
    assert review["debate"]["bear_case"]
    assert review["risk_committee"]["verdict"] == "blocked"
    assert "实盘阻断" in review["risk_committee"]["verdict_cn"]
    assert review["portfolio_committee"]["order_capability"] is False
    assert review["portfolio_committee"]["real_order_allowed"] is False
    assert review["order_capability"] is False


def test_multi_role_review_is_stable_for_the_same_evidence_and_never_fills_missing_fundamentals():
    first = _build_review()
    second = _build_review()

    assert first["review_id"] == second["review_id"]
    assert first["checkpoint"]["evidence_hash"] == second["checkpoint"]["evidence_hash"]
    fundamental = next(row for row in first["roles"] if row["role"] == "fundamental")
    assert fundamental["status"] == "partial"
    assert any("600438 缺少" in item for item in fundamental["missing_data"])
    assert "买入持有" in first["retrospective"]["compare_with"]
