from quant_data.trading.signal_fusion import SignalFusionEngine


def test_screening_total_is_audit_only_when_component_scores_exist():
    signal = SignalFusionEngine().fuse(
        symbol="300750",
        screening_score=95,
        fundamental_score=50,
        technical_score=50,
        information_score=50,
        fund_flow_score=50,
        market_score=50,
    )

    breakdown = signal.score_breakdown
    assert signal.final_score == 50
    assert "筛选底座" in breakdown["audit_only_dimensions"]
    assert all(row["key"] != "screening" for row in breakdown["contributions"])
    assert breakdown["normalized_weight_total"] == 1


def test_missing_dimension_reweights_only_valid_scores_and_closes_to_one():
    signal = SignalFusionEngine().fuse(
        symbol="600438",
        screening_score=88,
        fundamental_score=60,
        technical_score=70,
        information_score=None,
        fund_flow_score=55,
        market_score=None,
    )

    breakdown = signal.score_breakdown
    assert breakdown["normalized_weight_total"] == 1
    assert {row["key"] for row in breakdown["contributions"]} == {"fundamental", "technical", "fund_flow"}
    assert "近期信息" in breakdown["missing_dimensions"]


def test_invalid_score_is_excluded_instead_of_clamped_into_decision():
    signal = SignalFusionEngine().fuse(
        symbol="000001",
        screening_score=80,
        fundamental_score=60,
        technical_score=999,
        information_score=60,
        fund_flow_score=60,
        market_score=60,
    )

    assert signal.final_score == 60
    assert signal.score_breakdown["invalid_dimensions"][0]["key"] == "technical"
    assert all(row["key"] != "technical" for row in signal.score_breakdown["contributions"])


def test_screening_fallback_is_low_confidence_when_all_components_are_missing():
    signal = SignalFusionEngine().fuse(symbol="510300", screening_score=63)

    assert signal.final_score == 63
    assert signal.score_breakdown["screening_fallback_used"] is True
    assert signal.confidence <= 0.25
    assert signal.requires_manual_confirm is True

