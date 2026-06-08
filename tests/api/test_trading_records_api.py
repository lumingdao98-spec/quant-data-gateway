from fastapi.testclient import TestClient

import quant_data.api as api


def test_trading_records_api_lists_store_rows():
    api.trading_store_v323.put("orders", {"order_id": "unit-order", "symbol": "300750", "status": "accepted", "mode": "backtest"}, mode="backtest", symbol="300750", record_id="unit-order")

    data = TestClient(api.app).get("/api/trading-records?mode=backtest&symbol=300750").json()

    assert data["ok"] is True
    assert any(row.get("order_id") == "unit-order" for row in data["data"])
