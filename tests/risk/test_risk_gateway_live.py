from datetime import datetime

from quant_data.trading.risk_gateway import RiskGateway


def test_risk_gateway_blocks_live_like_stale_order():
    result = RiskGateway().evaluate_order(
        {"symbol": "300750", "side": "buy", "quantity": 100, "price": 100},
        portfolio={"cash": 100_000, "equity": 100_000},
        signal={"score": 80},
        quote={"last": 100},
        freshness={"action": "block"},
        now=datetime(2026, 6, 5, 10, 0, 0),
    )

    assert result["approved"] is False
    assert any("过期" in x for x in result["risk_reasons"])
