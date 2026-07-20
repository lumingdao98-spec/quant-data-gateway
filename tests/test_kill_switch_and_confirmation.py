from quant_data.live import LiveTradingEngine
from quant_data.persistence import TradingStore
from quant_data.trading.broker import BrokerConfig, SimulatorBrokerAdapter


def test_confirmation_required_and_kill_switch_blocks_before_broker(tmp_path):
    config = BrokerConfig(feature_live_broker=True, live_trading_enabled=True, order_confirm_required=True, max_daily_live_order_count=20)
    engine = LiveTradingEngine(config=config, broker=SimulatorBrokerAdapter(), store=TradingStore(tmp_path / "safety.sqlite"))
    payload = {"symbol": "300750", "side": "buy", "quantity": 100, "limit_price": 10}

    pending = engine.place_order(payload)
    engine.kill_switch(True)
    blocked = engine.place_order(payload, confirmed=True)

    assert pending["reason"] == "needs_confirmation"
    assert blocked["ok"] is False
    assert "KILL_SWITCH" in blocked["reason"]
