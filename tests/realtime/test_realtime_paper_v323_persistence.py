from quant_data.persistence import TradingStore
from quant_data.realtime import RealtimePaperEngineV323


def test_realtime_paper_tick_persists_session_orders_markers(tmp_path):
    store = TradingStore(tmp_path / "paper.sqlite")
    engine = RealtimePaperEngineV323(store=store)

    started = engine.start_session({"symbols": ["300750"], "interval_seconds": 15, "initial_cash": 100000})
    session_id = started["session"]["session_id"]
    tick = engine.tick(
        {
            "symbol": "300750",
            "price": 100,
            "quote": {"last": 100, "amount": 120_000_000, "volume": 2_000_000, "name": "宁德时代"},
            "fundamental_score": 82,
            "technical_score": 86,
            "information_score": 78,
            "market_score": 65,
            "is_trading_session": True,
        },
        session_id=session_id,
    )

    assert tick["ok"] is True
    assert store.get("paper_sessions", session_id)["symbols"] == ["300750"]
    assert store.list("signals", mode="realtime_paper", session_id=session_id)
    assert store.list("account_snapshots", mode="realtime_paper", session_id=session_id)
    assert store.list("chart_markers", mode="realtime_paper", session_id=session_id)

    restored = RealtimePaperEngineV323(store=store)
    assert restored.get_session(session_id)["status"] == "running"
