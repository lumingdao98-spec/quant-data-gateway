from fastapi.testclient import TestClient

import quant_data.api as api


class _CaptureLiveEngine:
    def __init__(self):
        self.calls = []

    def place_order(self, payload, *, confirmed=False):
        self.calls.append({"payload": payload, "confirmed": confirmed})
        return {"ok": True, "confirmed": confirmed}


def test_browser_confirmed_flag_cannot_bypass_server_confirmation_queue(monkeypatch):
    engine = _CaptureLiveEngine()
    monkeypatch.setattr(api, "live_trading_engine_v323", engine)
    monkeypatch.setattr(api, "_prepare_live_order_payload", lambda payload: dict(payload))

    result = TestClient(api.app).post(
        "/api/live/orders/place",
        json={"symbol": "300750", "side": "buy", "quantity": 100, "limit_price": 10, "confirmed": True},
    ).json()

    assert result["ok"] is True
    assert engine.calls[0]["confirmed"] is False

