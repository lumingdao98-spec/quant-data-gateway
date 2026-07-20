from quant_data.live import LiveTradingEngine
from quant_data.persistence import TradingStore
from quant_data.trading.broker import BrokerConfig, SimulatorBrokerAdapter


def test_live_batch_orders_enter_confirmation_individually(tmp_path):
    config = BrokerConfig(
        broker_type="simulator",
        feature_live_broker=True,
        live_trading_enabled=True,
        order_confirm_required=True,
        max_daily_live_order_count=20,
    )
    engine = LiveTradingEngine(config=config, broker=SimulatorBrokerAdapter(), store=TradingStore(tmp_path / "batch.sqlite"))

    result = engine.place_orders_batch(
        {"side": "buy", "quantity": 100, "limit_price": 10, "strategy_family": "short_term"},
        ["300750", "600438"],
    )

    assert result["count"] == 2
    assert all(row["result"]["reason"] == "needs_confirmation" for row in result["data"])
    assert len(engine.confirm_queue.list(status="pending")) == 2
