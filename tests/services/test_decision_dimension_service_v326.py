from quant_data.services.decision_dimension_service import DecisionDimensionService


def _ready_sources() -> dict:
    return {
        "fundamental": {"source": "财务披露快照", "quality_status": "available", "available_at": "2026-08-23 18:00:00"},
        "technical": {"source": "真实日K+分时", "quality_status": "available", "available_at": "2026-08-24 10:00:00"},
        "information": {"source": "公告正文快照", "quality_status": "full_text", "available_at": "2026-08-24 09:00:00"},
        "fund_flow": {"source": "真实量价/盘口快照", "quality_status": "proxy_available", "available_at": "2026-08-24 10:00:00"},
        "market": {"source": "五大指数+市场宽度", "quality_status": "available"},
    }


def test_three_dimensions_and_market_are_explained_for_paper_entry():
    result = DecisionDimensionService().evaluate(
        mode="realtime_paper",
        strategy_family="intraday_paper",
        scores={"fundamental": 64, "technical": 66, "information": 58, "fund_flow": 61, "market": 55},
        sources=_ready_sources(),
        freshness={"action": "allow"},
        recent_information={"auto_buy_eligible": True, "quality_status": "full_text"},
    )

    assert result["auto_entry_eligible"] is True
    assert all(row["ready"] for row in result["dimensions"])
    assert result["market_context"]["ready"] is True
    rows = {row["key"]: row for row in result["dimensions"]}
    assert "不得称为主力净流入" in rows["fund_flow"]["truth_boundary"]


def test_unusable_information_blocks_short_term_auto_entry():
    result = DecisionDimensionService().evaluate(
        mode="paper",
        strategy_family="short_term",
        scores={"technical": 72, "information": 70, "fund_flow": 68},
        sources=_ready_sources(),
        recent_information={"auto_buy_eligible": False, "quality_status": "title_only"},
    )

    assert result["auto_entry_eligible"] is False
    assert any("信息面未就绪" in reason for reason in result["entry_block_reasons"])


def test_backtest_excludes_non_pit_information_and_fund_flow_without_backfilling():
    sources = _ready_sources()
    sources["technical"]["pit_status"] = "point_in_time"
    result = DecisionDimensionService().evaluate(
        mode="backtest",
        strategy_family="swing",
        scores={"technical": 64, "information": 80, "fund_flow": 75},
        sources=sources,
        provenance={"no_lookahead": True, "mode": "backtest"},
    )

    rows = {row["key"]: row for row in result["dimensions"]}
    assert result["auto_entry_eligible"] is True
    assert rows["technical"]["ready"] is True
    assert rows["information"]["ready"] is False
    assert rows["fund_flow"]["ready"] is False
    assert "回测排除" in rows["information"]["reason"]


def test_live_buy_requires_current_live_provenance():
    result = DecisionDimensionService().evaluate(
        mode="live",
        strategy_family="short_term",
        scores={"technical": 70, "information": 62, "fund_flow": 64},
        sources=_ready_sources(),
        provenance={},
    )

    assert result["auto_entry_eligible"] is False
    assert "评分溯源" in "；".join(result["entry_block_reasons"])


def test_out_of_range_dimension_is_invalid_and_blocks_required_entry():
    result = DecisionDimensionService().evaluate(
        mode="paper",
        strategy_family="short_term",
        scores={"technical": 120, "information": 60, "fund_flow": 60},
        sources=_ready_sources(),
    )

    assert result["auto_entry_eligible"] is False
    assert result["dimensions"][0]["score"] is None
