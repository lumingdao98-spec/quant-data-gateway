from quant_data.trading.order_lifecycle import OrderLifecycle
from quant_data.trading.order_models import UnifiedOrder


def test_order_lifecycle_precheck_blocks_missing_provenance():
    order = UnifiedOrder(order_id="o1", session_id="s1", mode="live", symbol="300750", side="buy")

    out = OrderLifecycle().precheck(order, provenance_exists=False)

    assert out.status == "risk_blocked"
    assert "评分溯源" in out.status_reason
