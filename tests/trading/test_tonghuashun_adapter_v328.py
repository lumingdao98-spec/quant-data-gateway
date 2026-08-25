from __future__ import annotations

from quant_data.trading.broker import BrokerConfig, LiveOrderRequest, TonghuashunBridgeBrokerAdapter


def test_tonghuashun_bridge_rejects_unidentified_executor():
    def transport(method, path, payload):
        if path == "/health":
            return {"connected": True, "status": "connected", "provider": "unknown_bridge"}
        return {"ok": True}

    adapter = TonghuashunBridgeBrokerAdapter(
        BrokerConfig(
            broker_type="tonghuashun",
            http_bridge_url="http://127.0.0.1:8765",
            http_bridge_token="secret",
        ),
        transport=transport,
    )

    status = adapter.health_check()

    assert status.connected is False
    assert status.status == "blocked"
    assert status.broker == "tonghuashun_supermind_bridge"
    assert status.raw["provider_identity_verified"] is False


def test_tonghuashun_bridge_keeps_live_switches_as_hard_gate():
    calls: list[tuple[str, str]] = []

    def transport(method, path, payload):
        calls.append((method, path))
        if path == "/health":
            return {"connected": True, "status": "connected", "provider": "supermind"}
        if path == "/orders":
            return {"accepted": True, "order_id": "unsafe-order"}
        return {"ok": True}

    adapter = TonghuashunBridgeBrokerAdapter(
        BrokerConfig(
            broker_type="tonghuashun",
            http_bridge_url="http://127.0.0.1:8765",
            http_bridge_token="secret",
            feature_live_broker=False,
            live_trading_enabled=False,
        ),
        transport=transport,
    )

    ack = adapter.place_order(LiveOrderRequest(symbol="300750", side="buy", quantity=100, limit_price=300))

    assert ack.accepted is False
    assert ack.status == "rejected"
    assert ("POST", "/orders") not in calls
