from datetime import datetime

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.trading.order_manager import OrderManager
from quant_data.trading.paper_account import PaperAccount
from quant_data.trading.realtime_paper_engine import RealtimePaperEngine
from quant_data.trading.risk_gateway import RiskGateway


def test_paper_account_order_manager_records_cost_and_position():
    account = PaperAccount(initial_cash=100_000)
    manager = OrderManager(account)
    order = manager.build_order(symbol="300750", target_weight=0.2, side="buy", price=100, reason="unit buy")
    manager.simulate_fill(order, fill_price=100, fee_rate=0.0003, slippage_rate=0.0005)

    snap = account.snapshot()
    assert order.status == "filled"
    assert snap["positions"]["300750"]["quantity"] > 0
    assert snap["positions"]["300750"]["avg_cost"] > 100
    assert snap["cash"] < 100_000


def test_risk_gateway_rejects_stale_or_overweight_order():
    risk = RiskGateway()
    stale = risk.evaluate_order(
        {"symbol": "300750", "side": "buy", "quantity": 100, "price": 100},
        portfolio={"cash": 100_000, "equity": 100_000, "positions": {}},
        signal={"final_score": 70},
        freshness={"action": "block"},
        now=datetime(2026, 6, 1, 10, 0),
    )
    overweight = risk.evaluate_order(
        {"symbol": "300750", "side": "buy", "quantity": 1000, "price": 100},
        portfolio={"cash": 200_000, "equity": 100_000, "positions": {}},
        signal={"final_score": 70},
        quote={"amount": 100_000_000},
        freshness={"action": "allow"},
        now=datetime(2026, 6, 1, 10, 0),
    )

    assert stale["approved"] is False
    assert overweight["approved"] is False
    assert "risk_snapshot" in overweight


def test_realtime_paper_engine_blocks_non_trading_and_replays_without_lookahead():
    engine = RealtimePaperEngine()
    engine.start({"symbols": ["300750"], "initial_cash": 100_000})
    closed = engine.tick({"symbol": "300750", "price": 100, "ts": "2026-06-01T20:00:00", "technical_score": 80, "information_score": 70, "fundamental_score": 65, "market_score": 60})
    replay = engine.replay(
        {
            "symbol": "300750",
            "ticks": [
                {"price": 100, "ts": "2026-06-01T10:00:00", "technical_score": 82, "information_score": 70, "fundamental_score": 65, "market_score": 60},
                {"price": 101, "ts": "2026-06-01T10:01:00", "technical_score": 84, "information_score": 70, "fundamental_score": 65, "market_score": 60},
            ],
        }
    )

    assert closed["orders"] == []
    assert replay["no_lookahead"] is True
    assert len(replay["tick_log"]) == 2
    assert engine.audit(limit=20)["data"]


def test_realtime_paper_api_and_screener_bridge(monkeypatch):
    monkeypatch.setattr(api.watchlist_service, "add", lambda symbols: {"symbols": list(symbols), "count": len(symbols)})
    client = TestClient(api.app)
    started = client.post("/api/realtime-paper/start", json={"symbols": ["300750"], "initial_cash": 100_000}).json()
    tick = client.post(
        "/api/realtime-paper/tick",
        json={"symbol": "300750", "price": 100, "ts": "2026-06-01T10:00:00", "technical_score": 82, "information_score": 70, "fundamental_score": 65, "market_score": 60, "quote": {"amount": 100_000_000}},
    ).json()
    bridge = client.post("/api/screener/realtime-paper/add", json={"symbols": ["300750"], "rows": [{"symbol": "300750", "total_score": 72}]}).json()
    signal = client.post("/api/screener/signal-preview/300750", json={"row": {"symbol": "300750", "total_score": 72, "manual_review_score": 62}}).json()

    assert started["ok"] is True
    assert tick["ok"] is True
    assert bridge["ok"] is True
    assert signal["ok"] is True
    assert "signal" in signal
