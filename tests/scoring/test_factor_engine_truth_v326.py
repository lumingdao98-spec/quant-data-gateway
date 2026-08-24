from quant_data.scoring import V323FactorEngine


def test_missing_dimension_inputs_are_not_filled_with_neutral_scores():
    bundle = V323FactorEngine().compute(
        "300750",
        decision_time="2026-08-24 10:00:00",
        bars=[],
        quote={},
        fundamentals={},
        information={},
        fund_flow={},
        market_state={},
        behavior_risk={},
        data_sources=[],
    )

    assert bundle.values["technical_score"] is None
    assert bundle.values["fundamental_score"] is None
    assert bundle.values["information_score"] is None
    assert bundle.values["fund_flow_score"] is None
    assert bundle.values["market_regime_score"] is None
    assert bundle.values["behavior_risk_score"] is None
    assert bundle.values["data_quality_score"] == 35.0


def test_invalid_market_snapshot_is_excluded_even_when_it_contains_neutral_display_score():
    bundle = V323FactorEngine().compute(
        "300750",
        decision_time="2026-08-24 10:00:00",
        market_state={"score": 50, "valid_for_score": False},
    )

    assert bundle.values["market_regime_score"] is None
    assert any("大盘指数/宽度证据不足" in reason for reason in bundle.missing_data)
