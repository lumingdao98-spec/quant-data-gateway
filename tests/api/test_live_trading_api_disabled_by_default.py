from fastapi.testclient import TestClient

import quant_data.api as api


def test_live_trading_api_disabled_by_default():
    client = TestClient(api.app)

    status = client.get("/api/live-broker/status").json()
    placed = client.post("/api/live/orders/place", json={"symbol": "300750", "side": "buy", "quantity": 100, "limit_price": 100}).json()

    assert status["safety"]["LIVE_TRADING_ENABLED"] is False
    assert placed["ok"] is False


def test_live_batch_preview_does_not_bypass_safety():
    client = TestClient(api.app)

    data = client.post(
        "/api/live/orders/preview-batch",
        json={"symbols": "300750,600438", "side": "buy", "quantity": 100, "limit_price": 10},
    ).json()

    assert data["ok"] is True
    assert data["count"] == 2
    assert all("precheck" in row["preview"] for row in data["data"])
    assert all(row["preview"]["precheck"]["ok"] is False for row in data["data"])
    assert "不会绕过" in data["note"] or "不会" in data["note"]


def test_live_positions_include_normalized_pnl_fields():
    data = TestClient(api.app).get("/api/live/positions").json()

    assert data["ok"] is True
    assert "summary" in data
    assert "missing_reason" in data
    if data["data"]:
        row = data["data"][0]
        assert "cost_price" in row
        assert "last_price" in row
        assert "unrealized_pnl" in row
        assert "pnl_pct" in row
