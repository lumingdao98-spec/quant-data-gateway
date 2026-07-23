from quant_data.trading.human_confirm_queue import HumanConfirmQueue
from quant_data.trading.order_manager import OrderManager
from quant_data.trading.paper_account import PaperAccount
from quant_data.trading.realtime_paper_engine import RealtimePaperEngine


def test_paper_account_enforces_t_plus_one_and_sell_tax():
    account = PaperAccount(initial_cash=100_000)
    manager = OrderManager(account)
    buy = manager.build_order(symbol="300750", target_weight=0.10, side="buy", price=100, lot_size=100)

    manager.simulate_fill(
        buy,
        fill_price=100,
        filled_at="2026-07-20T10:00:00",
        t_plus_one=True,
    )

    position = account.snapshot()["positions"]["300750"]
    assert position["quantity"] == 100
    assert position["available_quantity"] == 0
    restored = PaperAccount.from_snapshot(account.snapshot())
    assert restored.positions["300750"].available_quantity == 0
    assert restored.pending_settlement["300750"][0]["quantity"] == 100
    blocked_preview = manager.preview_order(
        symbol="300750",
        target_weight=0,
        side="sell",
        price=101,
        lot_size=100,
    )
    assert blocked_preview["quantity"] == 0
    assert blocked_preview["available_quantity"] == 0

    account.settle_t_plus_one("2026-07-21")
    sell = manager.build_order(symbol="300750", target_weight=0, side="sell", price=101, lot_size=100)
    manager.simulate_fill(
        sell,
        fill_price=101,
        filled_at="2026-07-21T10:00:00",
        t_plus_one=True,
    )

    assert sell.status == "filled"
    assert account.fills[-1].fee == 5.0
    assert account.fills[-1].tax == 5.05
    assert account.snapshot()["positions"] == {}


def test_realtime_matcher_uses_best_ask_for_buy_fill():
    engine = RealtimePaperEngine()
    engine.start({"symbols": ["300750"], "initial_cash": 100_000})

    result = engine.tick(
        {
            "symbol": "300750",
            "price": 100,
            "ts": "2026-07-20T10:00:00",
            "quote": {
                "last": 100,
                "bid1": 99.95,
                "ask1": 100.05,
                "amount": 100_000_000,
                "ts": "2026-07-20T10:00:00",
            },
            "intraday_ts": "2026-07-20T10:00:00",
            "screening_score": 85,
            "daily_k_score": 85,
            "intraday_score": 85,
            "fundamental_score": 85,
            "technical_score": 85,
            "information_score": 85,
            "fund_flow_score": 85,
            "market_score": 85,
        },
        manual_replay=True,
    )

    assert result["orders"][0]["status"] == "filled"
    assert engine.account.fills[-1].price == 100.05
    assert engine.account.snapshot()["positions"]["300750"]["available_quantity"] == 0
    assert result["signal"]["market_rule"]["t_plus_one"] is True


def test_paper_confirmation_queue_deduplicates_same_pending_action():
    queue = HumanConfirmQueue()

    first = queue.enqueue(symbol="600438", action="buy", reason="大额订单", risk_flags=["人工确认"])
    second = queue.enqueue(symbol="600438", action="buy", reason="重复复评", risk_flags=["人工确认"])

    assert first.task_id == second.task_id
    assert len(queue.list(status="pending")) == 1
