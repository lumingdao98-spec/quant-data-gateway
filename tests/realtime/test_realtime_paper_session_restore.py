from quant_data.realtime import RealtimePaperEngineV323


def test_realtime_paper_session_start_and_restore():
    engine = RealtimePaperEngineV323()

    started = engine.start_session({"symbols": ["300750"], "interval_seconds": 15})
    session_id = started["session"]["session_id"]

    assert engine.get_session(session_id)["symbols"] == ["300750"]
