from quant_data.scoring import ScoreRequest, build_score_provenance_v323, explain_score


def test_v323_score_provenance_records_dimensions_sources_and_missing():
    src = {"source_id": "unit", "source_name": "unit", "missing_reasons": ["PB字段缺失"], "supports": ["technical_score"]}

    p = build_score_provenance_v323(
        ScoreRequest(
            symbol="300750",
            decision_time="2026-06-05 10:00:00",
            mode="realtime_paper",
            strategy_family="swing",
            factor_values={"technical_score": 70, "data_quality_score": 60},
            data_sources=[src],
        )
    )

    assert p.provenance_id.startswith("spv323-")
    assert p.missing_data == ["PB字段缺失"]
    assert explain_score(p)["symbol"] == "300750"
