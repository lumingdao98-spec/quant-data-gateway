from fastapi.testclient import TestClient

import quant_data.api as api


def test_trading_records_api_lists_store_rows():
    api.trading_store_v323.put("orders", {"order_id": "unit-order", "symbol": "300750", "status": "accepted", "mode": "backtest"}, mode="backtest", symbol="300750", record_id="unit-order")

    data = TestClient(api.app).get("/api/trading-records?mode=backtest&symbol=300750").json()

    assert data["ok"] is True
    assert any(row.get("order_id") == "unit-order" for row in data["data"])


def test_trading_records_api_enriches_amount_and_pnl_fields():
    api.trading_store_v323.put(
        "fills",
        {
            "fill_id": "unit-fill",
            "symbol": "600438",
            "side": "sell",
            "quantity": 200,
            "price": 14.5,
            "realized_pnl": 123.45,
            "mode": "live",
        },
        mode="live",
        symbol="600438",
        record_id="unit-fill",
    )

    data = TestClient(api.app).get("/api/trading-records?mode=live&symbol=600438").json()
    row = next(x for x in data["data"] if x.get("fill_id") == "unit-fill")

    assert row["record_type_cn"] == "成交"
    assert row["display_amount"] == 2900
    assert row["display_pnl"] == 123.45
    assert "金额" in row["display_summary"]
