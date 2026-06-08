from fastapi.testclient import TestClient

import quant_data.api as api


def test_live_trading_api_disabled_by_default():
    client = TestClient(api.app)

    status = client.get("/api/live-broker/status").json()
    placed = client.post("/api/live/orders/place", json={"symbol": "300750", "side": "buy", "quantity": 100, "limit_price": 100}).json()

    assert status["safety"]["LIVE_TRADING_ENABLED"] is False
    assert placed["ok"] is False
