from fastapi.testclient import TestClient
import pytest

import quant_data.api as api
from quant_data.persistence.trading_store import TradingStore


@pytest.fixture(autouse=True)
def isolated_trading_store(tmp_path, monkeypatch):
    store = TradingStore(tmp_path / "trading-records-test.sqlite")
    monkeypatch.setattr(api, "trading_store_v323", store)
    return store


def test_trading_records_api_lists_store_rows():
    api.trading_store_v323.put(
        "orders",
        {"order_id": "unit-order", "symbol": "300750", "status": "accepted", "mode": "backtest"},
        mode="backtest",
        symbol="300750",
        record_id="unit-order",
    )

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

    assert row["record_type_cn"] == "\u6210\u4ea4"
    assert row["display_amount"] == 2900
    assert row["display_pnl"] == 123.45
    assert "\u91d1\u989d" in row["display_summary"]


def test_trading_records_api_returns_summary_for_cost_and_pnl():
    api.trading_store_v323.put(
        "positions",
        {
            "position_id": "unit-summary-position",
            "symbol": "990001",
            "quantity": 100,
            "cost_price": 10,
            "last_price": 12,
            "market_value": 1200,
            "unrealized_pnl": 200,
            "unrealized_pnl_pct": 20,
            "mode": "unit_summary",
        },
        mode="unit_summary",
        symbol="990001",
        record_id="unit-summary-position",
    )
    api.trading_store_v323.put(
        "fills",
        {
            "fill_id": "unit-summary-fill",
            "symbol": "990001",
            "side": "sell",
            "quantity": 100,
            "price": 11,
            "fee": 5,
            "tax": 0.55,
            "slippage": 1.1,
            "realized_pnl": 100,
            "mode": "unit_summary",
        },
        mode="unit_summary",
        symbol="990001",
        record_id="unit-summary-fill",
    )

    data = TestClient(api.app).get("/api/trading-records?mode=unit_summary&symbol=990001").json()

    summary = data["summary"]
    assert data["ok"] is True
    assert summary["rows_count"] >= 2
    assert summary["fills_count"] >= 1
    assert summary["positions_count"] >= 1
    assert summary["position_market_value"] >= 1200
    assert summary["position_cost_value"] >= 1000
    assert summary["realized_pnl"] >= 100
    assert summary["unrealized_pnl"] >= 200
    assert summary["total_fee"] >= 6.65
    assert summary["symbol_counts"]["990001"] >= 2


def test_trading_records_enriches_position_cost_and_zero_pnl():
    row = api._enrich_trading_record_row(
        "positions",
        {
            "symbol": "300750",
            "quantity": 1000,
            "cost_price": 10.5,
            "last_price": 10.5,
            "market_value": 10500,
            "unrealized_pnl": 0,
            "unrealized_pnl_pct": 0,
        },
    )

    assert row["record_type_cn"] == "\u6301\u4ed3"
    assert row["display_price"] == 10.5
    assert row["display_quantity"] == 1000
    assert row["display_amount"] == 10500
    assert row["display_pnl"] == 0
    assert row["display_pnl_pct"] == 0
    assert row["display_cost_price"] == 10.5
    assert "\u6210\u672c 10.5" in row["display_summary"]
    assert "\u5e02\u503c 10500" in row["display_summary"]
    assert "\u6536\u76ca\u7387 0.0%" in row["display_summary"]


def test_trading_records_enriches_account_snapshot_as_account_record():
    row = api._enrich_trading_record_row(
        "account_snapshots",
        {
            "mode": "live",
            "total_value": 123456.78,
            "available_cash": 45678.9,
            "positions_market_value": 77777.88,
        },
    )

    assert row["record_type_cn"] == "\u8d26\u6237"
    assert row["display_amount"] == 123456.78
    assert row["display_price"] is None
    assert "\u91d1\u989d 123456.78" in row["display_summary"]
