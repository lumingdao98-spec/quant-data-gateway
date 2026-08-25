from quant_data.trading.broker import BrokerConfig, HttpBridgeBrokerAdapter, LiveOrderRequest
from quant_data.trading.broker.http_bridge_adapter import _order_status, _side


def _config(**overrides):
    values = {
        "broker_type": "http_bridge",
        "http_bridge_url": "http://127.0.0.1:9901",
        "http_bridge_token": "test-token",
        "feature_live_broker": True,
        "live_trading_enabled": True,
        "order_confirm_required": True,
    }
    values.update(overrides)
    return BrokerConfig(**values)


def test_http_bridge_is_unsupported_without_local_url_and_token():
    adapter = HttpBridgeBrokerAdapter(BrokerConfig(broker_type="http_bridge"))
    status = adapter.health_check()

    assert status.connected is False
    assert status.status == "unsupported"
    assert "BROKER_HTTP_URL" in status.message


def test_http_bridge_blocks_remote_host_by_default():
    adapter = HttpBridgeBrokerAdapter(_config(http_bridge_url="https://broker.example.com"))
    status = adapter.health_check()

    assert status.connected is False
    assert status.status == "blocked"


def test_http_bridge_never_places_when_live_flags_are_disabled():
    called = []
    adapter = HttpBridgeBrokerAdapter(
        _config(live_trading_enabled=False),
        transport=lambda method, path, payload: called.append((method, path, payload)) or {"accepted": True},
    )
    ack = adapter.place_order(LiveOrderRequest(symbol="300750", side="buy", quantity=100, limit_price=400))

    assert ack.accepted is False
    assert called == []


def test_http_bridge_accepts_only_explicit_success_from_authorized_bridge():
    calls = []

    def transport(method, path, payload):
        calls.append((method, path, payload))
        if path == "/health":
            return {"connected": True, "status": "connected", "message": "ok"}
        if path == "/orders":
            return {"accepted": True, "status": "accepted", "order_id": "bridge-1", "broker_order_id": "broker-9"}
        return {}

    adapter = HttpBridgeBrokerAdapter(_config(), transport=transport)
    status = adapter.health_check()
    ack = adapter.place_order(LiveOrderRequest(symbol="300750", side="buy", quantity=100, limit_price=400))

    assert status.connected is True
    assert ack.accepted is True
    assert ack.broker_order_id == "broker-9"
    assert calls[-1][1] == "/orders"


def test_http_bridge_malformed_or_negative_response_never_becomes_success():
    adapter = HttpBridgeBrokerAdapter(_config(), transport=lambda method, path, payload: {"status": "accepted"})
    ack = adapter.place_order(LiveOrderRequest(symbol="300750", side="buy", quantity=100, limit_price=400))

    assert ack.accepted is False


def test_http_bridge_normalizes_external_order_fields_without_guessing_unknown_side():
    assert _side("证券买入") == "buy"
    assert _side("卖出") == "sell"
    assert _side("other") == ""
    assert _order_status("部成") == "partially_filled"
    assert _order_status("已成") == "filled"
    assert _order_status("mystery") == "unknown"
