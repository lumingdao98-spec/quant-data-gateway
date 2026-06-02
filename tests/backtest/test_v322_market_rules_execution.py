from quant_data.backtest.execution import ExecutionSimulator
from quant_data.backtest.market_rules import MarketRuleEngine
from quant_data.backtest.models import BacktestConfig, Order, Position


def test_market_rule_engine_resolves_effective_profiles_from_config():
    engine = MarketRuleEngine.default()

    assert engine.resolve_profile("300750").profile_id == "SZSE_CHINEXT"
    assert engine.resolve_profile("600438").profile_id == "SSE_MAIN"
    assert engine.resolve_profile("510300").profile_id == "ETF_GENERIC"
    assert engine.resolve_profile("688599").price_limit_pct >= 0.19


def test_execution_uses_rule_profile_lot_size_and_odd_lot_sell():
    rules = MarketRuleEngine.from_dict(
        {
            "CUSTOM": {
                "exchange": "UNIT",
                "board": "UNIT",
                "security_type": "stock",
                "lot_size_buy": 200,
                "odd_lot_sell_once": True,
                "price_limit_pct": 0.10,
            }
        }
    )
    sim = ExecutionSimulator(rule_engine=rules)
    bar = {
        "ts": "2026-01-02",
        "open": 10.0,
        "high": 10.3,
        "low": 9.8,
        "close": 10.1,
        "volume": 100_000,
        "price_limit_profile_id": "CUSTOM",
    }
    cfg = BacktestConfig(volume_limit_pct=1.0, min_trade_amount=0.0)

    buy = sim.execute_order(
        Order("o-buy", "000001", "2026-01-01", "buy", quantity=350, signal_date="2026-01-01"),
        bar,
        cash=10_000,
        config=cfg,
    )
    assert buy.fill is not None
    assert buy.fill.quantity == 200

    sell = sim.execute_order(
        Order("o-sell", "000001", "2026-01-01", "sell", quantity=150, signal_date="2026-01-01"),
        bar,
        cash=0,
        position=Position("000001", quantity=150, available_quantity=150, avg_cost=9.5, last_price=10),
        config=cfg,
    )
    assert sell.fill is not None
    assert sell.fill.quantity == 150
