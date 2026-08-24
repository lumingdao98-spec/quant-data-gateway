from quant_data.realtime import RealtimeSignalLoop


def test_realtime_signal_loop_keeps_missing_source_reasons():
    out = RealtimeSignalLoop().run_once(
        "300750",
        {"technical_score": 60, "data_quality_score": 30},
        data_sources=[{"source_id": "missing", "source_name": "数据源缺失", "missing_reasons": ["盘口缺失"]}],
        decision_time="2026-06-05 10:00:00",
    )

    assert out["provenance"]["missing_data"] == ["盘口缺失"]
    assert set(out["provenance"]["dimension_scores"]) == {"technical_score", "data_quality_score"}
    assert out["provenance"]["excluded_dimensions"]
