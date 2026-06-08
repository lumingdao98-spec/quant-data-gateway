from quant_data.live import LiveTradingEngine


def test_live_kill_switch_blocks_order():
    engine = LiveTradingEngine()
    engine.kill_switch(True)

    result = engine.place_order({"symbol": "300750", "side": "buy", "quantity": 100, "limit_price": 100})

    assert result["ok"] is False
    assert "KILL" in result["reason"]
