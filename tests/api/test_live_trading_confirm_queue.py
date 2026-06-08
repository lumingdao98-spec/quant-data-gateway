from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.trading.broker import BrokerConfig
from quant_data.live import LiveTradingEngine


def test_live_confirm_queue_endpoint(monkeypatch):
    engine = LiveTradingEngine(config=BrokerConfig(feature_live_broker=True, live_trading_enabled=True, trade_whitelist_symbols=["300750"], max_live_order_value=99_999))
    monkeypatch.setattr(api, "live_trading_engine_v323", engine)
    client = TestClient(api.app)

    result = client.post("/api/live/orders/place", json={"symbol": "300750", "side": "buy", "quantity": 100, "limit_price": 10}).json()
    queue = client.get("/api/live/confirm-queue").json()

    assert result["reason"] == "needs_confirmation"
    assert queue["count"] == 1
