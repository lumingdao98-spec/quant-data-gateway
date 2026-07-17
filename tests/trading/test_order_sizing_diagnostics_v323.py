from quant_data.trading.order_manager import OrderManager
from quant_data.trading.paper_account import PaperAccount


def test_high_price_below_minimum_lot_returns_actionable_diagnostic():
    manager = OrderManager(PaperAccount(initial_cash=100_000))

    preview = manager.preview_order(
        symbol="300750",
        target_weight=0.20,
        side="buy",
        price=380,
    )

    assert preview["quantity"] == 0
    assert preview["status"] == "below_minimum_lot"
    assert preview["minimum_lot_value"] == 38_000
    assert preview["minimum_account_equity"] == 190_000
    assert "最小买入100股" in preview["message"]


def test_low_price_symbol_keeps_a_share_lot_rounding():
    manager = OrderManager(PaperAccount(initial_cash=100_000))

    preview = manager.preview_order(
        symbol="600438",
        target_weight=0.20,
        side="buy",
        price=12,
    )

    assert preview["quantity"] == 1_600
    assert preview["status"] == "executable"
