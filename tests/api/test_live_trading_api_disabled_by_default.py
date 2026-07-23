from fastapi.testclient import TestClient

import quant_data.api as api


def test_live_trading_api_disabled_by_default():
    client = TestClient(api.app)

    status = client.get("/api/live-broker/status").json()
    placed = client.post(
        "/api/live/orders/place",
        json={"symbol": "300750", "side": "buy", "quantity": 100, "limit_price": 100},
    ).json()

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
    assert data["note"]


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


def test_live_orders_separate_prechecks_from_actual_broker_orders():
    client = TestClient(api.app)
    client.post(
        "/api/live/orders/preview",
        json={"symbol": "300750", "side": "buy", "quantity": 100, "limit_price": 10},
    )

    actual = client.get("/api/live/orders?scope=actual").json()
    prechecks = client.get("/api/live/orders?scope=precheck").json()

    assert actual["ok"] is True
    assert all(row["is_actual_broker_order"] is True for row in actual["data"])
    assert prechecks["ok"] is True
    assert any(row["symbol"] == "300750" for row in prechecks["data"])
    assert all(row["record_stage"] in {"precheck", "risk_blocked"} for row in prechecks["data"])
    assert prechecks["summary"]["precheck_or_blocked"] >= 1


def test_live_account_reports_unavailable_instead_of_real_zero_balance():
    data = TestClient(api.app).get("/api/live/account").json()

    assert data["ok"] is True
    assert data["data_available"] is False
    assert data["missing_reason"]
