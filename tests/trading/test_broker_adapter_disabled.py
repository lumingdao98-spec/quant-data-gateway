from quant_data.trading.broker import DisabledBrokerAdapter, LiveOrderRequest


def test_disabled_broker_rejects_real_orders():
    broker = DisabledBrokerAdapter()

    ack = broker.place_order(LiveOrderRequest(symbol="300750", side="buy", quantity=100, limit_price=100))

    assert ack.accepted is False
    assert broker.health_check().status == "disabled"
