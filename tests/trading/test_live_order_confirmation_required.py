from quant_data.live import LiveTradingEngine
from quant_data.persistence.trading_store import TradingStore
from quant_data.trading.broker import BrokerConfig


def test_live_order_needs_flags_before_confirmation():
    engine = LiveTradingEngine(config=BrokerConfig(feature_live_broker=False, live_trading_enabled=False))

    result = engine.place_order({"symbol": "300750", "side": "buy", "quantity": 100, "limit_price": 100})

    assert result["ok"] is False
    assert "未开启" in result["reason"]


def test_pending_confirmations_do_not_count_as_submitted_live_orders(tmp_path):
    store = TradingStore(tmp_path / "trading.sqlite")
    config = BrokerConfig(
        feature_live_broker=True,
        live_trading_enabled=True,
        trade_whitelist_symbols=["300750"],
        max_daily_live_order_count=1,
        max_live_order_value=99_999,
    )
    engine = LiveTradingEngine(config=config, store=store)

    first = engine.place_order({"symbol": "300750", "side": "buy", "quantity": 100, "limit_price": 10})
    second = engine.place_order({"symbol": "300750", "side": "buy", "quantity": 100, "limit_price": 10})

    assert first["reason"] == "needs_confirmation"
    assert second["reason"] == "needs_confirmation"
    assert engine._daily_live_order_count() == 0
