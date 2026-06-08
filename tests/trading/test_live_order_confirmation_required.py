from quant_data.live import LiveTradingEngine
from quant_data.trading.broker import BrokerConfig


def test_live_order_needs_flags_before_confirmation():
    engine = LiveTradingEngine(config=BrokerConfig(feature_live_broker=False, live_trading_enabled=False))

    result = engine.place_order({"symbol": "300750", "side": "buy", "quantity": 100, "limit_price": 100})

    assert result["ok"] is False
    assert "未开启" in result["reason"]
