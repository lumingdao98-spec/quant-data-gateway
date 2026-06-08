from quant_data.scoring import ScoreRequest, SignalFusionV323, build_score_provenance_v323


def test_signal_fusion_requires_confirmation_message_for_live():
    p = build_score_provenance_v323(
        ScoreRequest(
            symbol="300750",
            decision_time="2026-06-05",
            mode="live",
            strategy_family="swing",
            factor_values={"technical_score": 90, "fundamental_score": 80, "data_quality_score": 90},
            data_sources=[{"source_id": "unit", "source_name": "unit"}],
        )
    )

    sig = SignalFusionV323().fuse(p)

    assert sig.action == "buy"
    assert "人工确认" in sig.reason
