from quant_data.scoring.adaptive_execution_policy import AdaptiveExecutionPolicy
from quant_data.trading.signal_fusion import SignalFusionEngine


def test_strategy_profiles_change_weights_without_changing_neutral_swing_defaults():
    policy = AdaptiveExecutionPolicy()

    swing = policy.resolve(strategy_family="swing", market_score=50)
    short = policy.resolve(strategy_family="short", market_score=50)
    position = policy.resolve(strategy_family="position", market_score=50)
    dca = policy.resolve(strategy_family="dca", market_score=50)

    assert swing.weights == {
        "fundamental": 0.22,
        "technical": 0.30,
        "information": 0.20,
        "fund_flow": 0.16,
        "market": 0.12,
    }
    assert short.weights["technical"] > swing.weights["technical"]
    assert short.weights["fund_flow"] > swing.weights["fund_flow"]
    assert position.weights["fundamental"] > swing.weights["fundamental"]
    assert dca.weights["fundamental"] == 0
    assert dca.weights["market"] > swing.weights["market"]


def test_market_regime_adjustment_is_bounded_and_explained():
    policy = AdaptiveExecutionPolicy()

    weak = policy.resolve(strategy_family="swing", market_score=30)
    strong = policy.resolve(strategy_family="swing", market_score=75)
    missing = policy.resolve(strategy_family="swing", market_score=None)

    assert weak.market_band == "弱势"
    assert weak.thresholds["buy"] == 66
    assert weak.position_scale == 0.60
    assert round(sum(weak.weights.values()), 7) == 1
    assert strong.thresholds["buy"] == 61
    assert strong.position_scale == 1
    assert missing.market_band == "证据不足"
    assert missing.thresholds["buy"] == 64
    assert missing.position_scale <= 0.75
    assert all(row for row in weak.rationale)


def test_manual_weights_win_but_market_risk_still_changes_threshold_and_position():
    policy = AdaptiveExecutionPolicy()
    decision = policy.resolve(
        strategy_family="short",
        market_score=25,
        score_weights={
            "mode": "manual",
            "fundamental": 10,
            "technical": 20,
            "information": 30,
            "fund_flow": 30,
            "market": 10,
        },
    )

    assert decision.weight_mode == "manual"
    assert decision.weights == {
        "fundamental": 0.1,
        "technical": 0.2,
        "information": 0.3,
        "fund_flow": 0.3,
        "market": 0.1,
    }
    assert decision.thresholds["buy"] == 66
    assert decision.position_scale == 0.60


def test_signal_fusion_uses_resolved_thresholds_and_persists_policy():
    signal = SignalFusionEngine().fuse(
        symbol="300750",
        strategy_family="short",
        market_score=30,
        fundamental_score=64,
        technical_score=64,
        information_score=64,
        fund_flow_score=64,
        anomaly_score=0,
    )

    contribution_total = sum(row["contribution"] for row in signal.score_breakdown["contributions"])
    assert signal.final_score == round(contribution_total, 2)
    assert signal.final_score < signal.score_breakdown["thresholds"]["buy"]
    assert signal.action == "hold"
    assert signal.score_breakdown["thresholds"]["buy"] == 66
    assert signal.score_breakdown["adaptive_policy"]["strategy_family"] == "short"
    assert signal.target_weight < 0.25
