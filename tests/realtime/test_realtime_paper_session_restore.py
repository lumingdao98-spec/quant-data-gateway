from quant_data.realtime import RealtimePaperEngineV323
from quant_data.persistence import TradingStore
from quant_data.trading.paper_account import PaperFill


def test_realtime_paper_session_start_and_restore():
    engine = RealtimePaperEngineV323()

    started = engine.start_session({"symbols": ["300750"], "interval_seconds": 15})
    session_id = started["session"]["session_id"]

    assert engine.get_session(session_id)["symbols"] == ["300750"]


def test_realtime_paper_restores_cash_positions_and_fills_without_double_debit(tmp_path):
    store = TradingStore(tmp_path / "paper_restore.sqlite")
    engine = RealtimePaperEngineV323(store=store)
    session_id = engine.start_session(
        {"symbols": ["600438"], "initial_cash": 100_000, "interval_seconds": 15}
    )["session"]["session_id"]
    account = engine.engines[session_id].account
    account.apply_fill(
        PaperFill(
            order_id="buy-1",
            symbol="600438",
            side="buy",
            quantity=1_000,
            price=12.0,
            amount=12_000.0,
            fee=3.6,
        )
    )
    engine.sync_engine_state(session_id)
    cash_before = account.cash

    restored = RealtimePaperEngineV323(store=store)
    restored_account = restored.engines[session_id].account

    assert restored_account.cash == cash_before
    assert restored_account.positions["600438"].quantity == 1_000
    assert restored_account.positions["600438"].avg_cost > 12.0
    assert restored_account.fills[0].order_id == "buy-1"


def test_realtime_paper_parallel_sessions_do_not_share_positions(tmp_path):
    engine = RealtimePaperEngineV323(store=TradingStore(tmp_path / "paper_isolation.sqlite"))
    first_id = engine.start_session({"symbols": ["600438"], "initial_cash": 100_000})["session"]["session_id"]
    second_id = engine.start_session(
        {"symbols": ["300750"], "initial_cash": 300_000, "parallel_session": True}
    )["session"]["session_id"]

    engine.engines[first_id].account.apply_fill(
        PaperFill(order_id="first-buy", symbol="600438", side="buy", quantity=100, price=12, amount=1_200)
    )
    engine.sync_engine_state(first_id)
    engine.sync_engine_state(second_id)

    assert "600438" in engine.engines[first_id].account.positions
    assert engine.engines[second_id].account.positions == {}
    assert engine.portfolio(first_id)["data"]["positions"]["600438"]["quantity"] == 100
    assert engine.portfolio(second_id)["data"]["positions"] == {}


def test_realtime_paper_update_active_session_keeps_account_history(tmp_path):
    engine = RealtimePaperEngineV323(store=TradingStore(tmp_path / "paper_update.sqlite"))
    session_id = engine.start_session(
        {"symbols": ["600438"], "initial_cash": 100_000, "reset_account": True}
    )["session"]["session_id"]
    account = engine.engines[session_id].account
    account.apply_fill(
        PaperFill(order_id="keep-buy", symbol="600438", side="buy", quantity=100, price=12, amount=1_200)
    )
    engine.sync_engine_state(session_id)

    updated = engine.update_active_session(
        {
            "symbols": ["600438", "510300"],
            "strategy_family": "swing",
            "interval_seconds": 30,
            "initial_cash": 50_000,
            "reset_account": False,
        }
    )

    assert updated["ok"] is True
    assert updated["account_preserved"] is True
    assert updated["session"]["session_id"] == session_id
    assert updated["session"]["symbols"] == ["600438", "510300"]
    assert engine.engines[session_id].account.initial_cash == 100_000
    assert engine.engines[session_id].account.positions["600438"].quantity == 100
    assert engine.engines[session_id].account.fills[0].order_id == "keep-buy"


def test_realtime_score_combines_screener_daily_k_and_intraday(tmp_path):
    engine = RealtimePaperEngineV323(store=TradingStore(tmp_path / "paper_composite_score.sqlite"))
    session_id = engine.start_session(
        {
            "symbols": ["600438"],
            "screener_snapshot_id": "screen-1",
            "screener_signal_map": {
                "600438": {
                    "name": "通威股份",
                    "final_score": 68,
                    "technical_score": 60,
                    "fundamental_score": 58,
                    "information_score": 55,
                    "fund_flow_score": 52,
                    "market_score": 50,
                    "source": "screener_snapshot",
                }
            },
            "score_weights": {"screening": 0.30, "technical": 0.28, "fundamental": 0.16, "information": 0.10, "fund_flow": 0.10, "market": 0.06},
        }
    )["session"]["session_id"]

    weak = engine.tick(
        {
            "session_id": session_id,
            "symbol": "600438",
            "price": 12.0,
            "intraday_score": 40,
            "technical_score": 40,
            "score_source": "realtime_quote_intraday_v323",
        },
        manual_replay=True,
    )["signal"]
    strong = engine.tick(
        {
            "session_id": session_id,
            "symbol": "600438",
            "price": 12.2,
            "intraday_score": 80,
            "technical_score": 80,
            "score_source": "realtime_quote_intraday_v323",
        },
        manual_replay=True,
    )["signal"]

    assert weak["screening_score"] == strong["screening_score"] == 68
    assert weak["daily_k_score"] == strong["daily_k_score"] == 60
    assert weak["intraday_score"] == 40
    assert strong["intraday_score"] == 80
    assert weak["technical_score"] < strong["technical_score"]
    assert weak["final_score"] < strong["final_score"]
    assert strong["score_breakdown"]["screener_snapshot_id"] == "screen-1"


def test_realtime_signal_persists_score_provenance_and_links_orders(tmp_path):
    store = TradingStore(tmp_path / "paper_score_provenance.sqlite")
    engine = RealtimePaperEngineV323(store=store)
    session_id = engine.start_session(
        {
            "symbols": ["600438"],
            "initial_cash": 100_000,
            "screener_snapshot_id": "screen-live-1",
            "screener_signal_map": {
                "600438": {
                    "name": "通威股份",
                    "final_score": 72,
                    "technical_score": 70,
                    "fundamental_score": 68,
                    "information_score": 66,
                    "fund_flow_score": 70,
                    "market_score": 62,
                    "source": "screener_snapshot",
                }
            },
        }
    )["session"]["session_id"]

    engine.tick(
        {
            "session_id": session_id,
            "symbol": "600438",
            "price": 12.0,
            "intraday_score": 76,
            "technical_score": 76,
            "fund_flow_score": 74,
            "market_score": 64,
            "score_source": "realtime_quote_intraday_v323",
            "recent_information": {
                "snapshot_id": "info-live-1",
                "source_id": "official_news_cache",
                "source_name": "近期官方信息",
                "quality_status": "fresh",
            },
        },
        manual_replay=True,
    )
    counts = engine.sync_engine_state(session_id)

    provenances = store.list("score_provenance", mode="realtime_paper", session_id=session_id)
    signals = store.list("signals", mode="realtime_paper", session_id=session_id)
    orders = store.list("orders", mode="realtime_paper", session_id=session_id)

    assert counts["score_provenance"] >= 1
    assert provenances
    assert provenances[0]["mode"] == "realtime_paper"
    assert provenances[0]["screener_snapshot_id"] == "screen-live-1"
    assert provenances[0]["information_snapshot_id"] == "info-live-1"
    assert provenances[0]["final_score"] == signals[0]["final_score"]
    assert signals[0]["provenance_id"] == provenances[0]["provenance_id"]
    assert all(row["provenance_id"] == provenances[0]["provenance_id"] for row in orders)

    provenance_ids = {row["provenance_id"] for row in provenances}
    engine.sync_engine_state(session_id)
    repeated = store.list("score_provenance", mode="realtime_paper", session_id=session_id)

    assert len(repeated) == len(provenances)
    assert {row["provenance_id"] for row in repeated} == provenance_ids
