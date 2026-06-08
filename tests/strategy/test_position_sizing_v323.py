from quant_data.strategy import PositionSizingEngine


def test_position_sizing_engine_wraps_shared_sizer():
    decision = PositionSizingEngine().size(
        {"symbol": "300750", "score": 75, "target_weight": 0.2},
        {"cash": 100_000, "equity": 100_000},
        {"stop_distance_pct": 0.08},
        {"symbol": "300750"},
        {"close": 100, "atr": 5},
        {"sizing_mode": "score_weighted", "min_trade_amount": 0},
    )

    assert decision.quantity >= 0
    assert "actual_weight" in decision.to_dict()
