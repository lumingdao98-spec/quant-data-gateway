from quant_data.realtime.realtime_paper_engine import RealtimePaperEngineV323
from quant_data.persistence import TradingStore
from quant_data.strategy import get_strategy_execution_profile, normalize_strategy_family


def test_strategy_aliases_share_canonical_profile_hash():
    assert normalize_strategy_family("short_term") == "short"
    assert normalize_strategy_family("long_term") == "position"
    assert normalize_strategy_family("hybrid") == "core_satellite"
    assert get_strategy_execution_profile("short_term").profile_hash == get_strategy_execution_profile("short").profile_hash


def test_realtime_session_persists_canonical_profile(tmp_path):
    engine = RealtimePaperEngineV323(store=TradingStore(tmp_path / "strategy.sqlite"))
    result = engine.start_session({"symbols": ["300750"], "strategy_family": "hybrid"})

    session = result["session"]
    assert session["strategy_family"] == "core_satellite"
    assert session["strategy_profile"]["profile_hash"] == get_strategy_execution_profile("core_satellite").profile_hash
