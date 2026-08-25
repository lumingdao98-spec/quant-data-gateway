from __future__ import annotations

import pytest

from quant_data.scoring import ScoreRequest, build_score_provenance_v323
from quant_data.scoring.score_policy import ScorePolicyV323


def test_v328_policy_matches_execution_dimensions_and_quality_is_gate_only():
    policy = ScorePolicyV323()

    assert policy.policy_version == "v3.28-execution-aligned"
    assert policy.dimension_weights["fundamental_score"] == pytest.approx(0.22)
    assert policy.dimension_weights["technical_score"] == pytest.approx(0.30)
    assert policy.dimension_weights["information_score"] == pytest.approx(0.20)
    assert policy.dimension_weights["fund_flow_score"] == pytest.approx(0.16)
    assert policy.dimension_weights["market_regime_score"] == pytest.approx(0.12)
    assert policy.dimension_weights["data_quality_score"] == 0.0
    assert sum(weight for weight in policy.dimension_weights.values() if weight > 0) == pytest.approx(1.0)


def test_low_data_quality_blocks_new_position_without_adding_score():
    provenance = build_score_provenance_v323(
        ScoreRequest(
            symbol="300750",
            decision_time="2026-08-25 10:00:00",
            mode="realtime_paper",
            strategy_family="swing",
            factor_values={
                "fundamental_score": 80,
                "technical_score": 80,
                "information_score": 80,
                "fund_flow_score": 80,
                "market_regime_score": 80,
                "behavior_risk_score": 0,
                "data_quality_score": 30,
            },
            data_sources=[{"source_id": "unit", "source_name": "unit"}],
        )
    )

    quality = next(row for row in provenance.factor_contributions if row.factor_key == "data_quality_score")
    assert quality.weight == 0.0
    assert quality.contribution == 0.0
    assert "不参与加权得分" in quality.explanation
    assert any(gate.gate_key == "data_quality_low_block" and not gate.passed for gate in provenance.gates)


def test_missing_data_quality_blocks_realtime_but_not_backtest_score_math():
    realtime = build_score_provenance_v323(
        ScoreRequest(
            symbol="300750",
            decision_time="2026-08-25 10:00:00",
            mode="live",
            factor_values={"technical_score": 70},
            data_sources=[{"source_id": "unit"}],
        )
    )
    backtest = build_score_provenance_v323(
        ScoreRequest(
            symbol="300750",
            decision_time="2024-08-25 15:00:00",
            mode="backtest",
            factor_values={"technical_score": 70},
            data_sources=[{"source_id": "pit"}],
        )
    )

    assert any(gate.gate_key == "data_quality_missing_block" for gate in realtime.gates)
    assert not any(gate.gate_key.startswith("data_quality_") for gate in backtest.gates)
