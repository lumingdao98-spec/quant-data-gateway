from datetime import datetime, timedelta

from quant_data.factors.score_provenance import FactorValue, GateResult, ScoringPolicy, build_score_provenance


def test_score_provenance_excludes_future_factor_and_records_coverage():
    asof = datetime(2026, 6, 1, 15, 0)
    factors = [
        FactorValue(
            factor_id="f-trend",
            symbol="300750",
            asof_time=asof.isoformat(timespec="seconds"),
            factor_key="trend_score",
            raw_value=72,
            normalized_value=72,
            weight=8,
            source_refs=["pit:kline"],
            available_at=asof.isoformat(timespec="seconds"),
            group="technical",
        ),
        FactorValue(
            factor_id="f-news",
            symbol="300750",
            asof_time=asof.isoformat(timespec="seconds"),
            factor_key="future_news_score",
            raw_value=95,
            normalized_value=95,
            weight=20,
            source_refs=["future:news"],
            available_at=(asof + timedelta(hours=2)).isoformat(timespec="seconds"),
            group="information",
        ),
    ]

    provenance = build_score_provenance(
        "300750",
        decision_time=asof,
        asof_time=asof,
        strategy_family="short_term_momentum",
        factor_values=factors,
        gate_results=[GateResult("stale_data", True, source_refs=["pit:quote"])],
        scoring_policy=ScoringPolicy(weights={"trend_score": 8, "future_news_score": 20}),
    )

    data = provenance.to_dict()
    assert data["coverage_pct"] == 50.0
    assert data["no_lookahead"] is False
    assert any(not item["used"] for item in data["contributions"])
    assert "future:news" in data["source_refs"]
    assert data["final_score"] < 70
