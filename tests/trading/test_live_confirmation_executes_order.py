from quant_data.live import LiveTradingEngine
from quant_data.persistence import TradingStore
from quant_data.trading.broker import BrokerConfig


def test_live_confirmation_approval_routes_original_order_to_broker(tmp_path):
    store = TradingStore(tmp_path / "live.sqlite")
    engine = LiveTradingEngine(
        config=BrokerConfig(
            broker_type="simulator",
            feature_live_broker=True,
            live_trading_enabled=True,
            order_confirm_required=True,
            trade_whitelist_symbols=["300750"],
            max_live_order_value=100_000,
        ),
        store=store,
    )

    placed = engine.place_order({"symbol": "300750", "side": "buy", "quantity": 100, "limit_price": 10})
    confirm_id = placed["confirmation"]["task_id"]
    approved = engine.approve_confirmation(confirm_id)

    assert placed["reason"] == "needs_confirmation"
    assert approved["ok"] is True
    assert approved["execution"]["data"]["broker_ack"]["status"] == "accepted"
    assert store.get("manual_confirmations", confirm_id)["status"] == "approved"
    assert store.list("orders", mode="live", symbol="300750")
    assert store.list("broker_raw_responses", mode="live", symbol="300750")
    assert store.list("chart_markers", mode="live", symbol="300750")
