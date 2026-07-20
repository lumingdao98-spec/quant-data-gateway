from quant_data.persistence import TradingStore
from quant_data.trading.ledger import LedgerService


def test_fill_creates_trade_fee_tax_and_slippage_ledger_entries(tmp_path):
    store = TradingStore(tmp_path / "ledger.sqlite")
    service = LedgerService(store)

    rows = service.record_fill(
        {"fill_id": "f1", "order_id": "o1", "symbol": "600438", "side": "sell", "quantity": 200, "price": 15, "fee": 5, "tax": 3, "slippage": 2},
        mode="live",
        session_id="s1",
        account_id="a1",
        source="broker:unit",
    )

    assert {row["entry_type"] for row in rows} == {"sell", "commission", "tax", "slippage"}
    assert sum(row["amount"] for row in rows) == 2990
    assert all(row["entry_id"] for row in rows)
