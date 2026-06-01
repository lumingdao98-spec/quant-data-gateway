from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.backtest.execution import ExecutionSimulator
from quant_data.backtest.exit_policy import ExitPolicy
from quant_data.backtest.historical_snapshot import HistoricalScreenerSnapshotBuilder
from quant_data.backtest.models import BacktestConfig, Order, Position, StrategySignal
from quant_data.backtest.portfolio import PortfolioManager
from quant_data.backtest.quality_filter import StrategyQualityFilter
from quant_data.backtest.rebalance import RebalanceEngine
from quant_data.backtest.risk import calculate_metrics
from quant_data.backtest.walk_forward import WalkForwardValidator
from quant_data.trading import PaperTradingGateway, TradingSignal


def _bar(date: str = "2025-01-02", **kwargs):
    base = {"date": date, "open": 10.0, "high": 10.5, "low": 9.8, "close": 10.2, "volume": 1_000_000, "amount": 10_000_000}
    base.update(kwargs)
    return base


def _bars(count: int = 90):
    rows = []
    for i in range(count):
        price = 10 + i * 0.05
        rows.append(_bar(f"2025-01-{(i % 28) + 1:02d}", open=price, high=price * 1.02, low=price * 0.98, close=price * 1.01))
    return rows


def test_engine_selection_default_v320_and_legacy_explicit(monkeypatch):
    monkeypatch.setattr(api.service, "get_quote", lambda *a, **k: None)
    monkeypatch.setattr(api.service, "get_kline", lambda *a, **k: _bars(120))
    client = TestClient(api.app)

    default = client.get("/api/backtest/run?symbol=300750&limit=120").json()
    legacy = client.get("/api/backtest/run?symbol=300750&limit=120&legacy=true").json()

    assert default["ok"] is True
    assert default["data"]["engine_version"] == "v3.20"
    assert legacy["ok"] is True
    assert legacy["data"]["legacy"] is True
    assert "legacy 快速验证" in legacy["data"]["legacy_warning"]


def test_slippage_not_double_counted_in_price_adjusted_mode():
    cfg = BacktestConfig(initial_cash=2_000, slippage_bps=100, slippage_mode="price_adjusted_slippage", t_plus_one=False, min_commission=0, transfer_fee_rate=0)
    sim = ExecutionSimulator()
    order = Order("o1", "600438", "2025-01-02", "buy", quantity=100, signal_date="2025-01-01")
    decision = sim.execute_order(order, _bar(open=10), cash=2_000, config=cfg)

    assert decision.fill is not None
    fill = decision.fill
    assert fill.price == 10.1
    assert fill.slippage_cost > 0
    pm = PortfolioManager(cfg)
    pm.apply_fill(fill)
    expected_cash = 2_000 - fill.gross_amount - fill.commission - fill.transfer_fee
    assert round(pm.cash, 6) == round(expected_cash, 6)


def test_explicit_slippage_cost_is_cash_cost():
    cfg = BacktestConfig(slippage_bps=100, slippage_mode="explicit_slippage_cost", t_plus_one=False, min_commission=0, transfer_fee_rate=0)
    sim = ExecutionSimulator()
    fill = sim.execute_order(Order("o1", "600438", "2025-01-02", "buy", quantity=100, signal_date="2025-01-01"), _bar(open=10), cash=2_000, config=cfg).fill

    assert fill is not None
    assert fill.price == 10
    assert fill.cash_cost >= fill.slippage_cost > 0


def test_limit_order_touch_and_expire():
    cfg = BacktestConfig(order_type="limit", order_valid_days=2, slippage_bps=0, t_plus_one=False, min_commission=0)
    sim = ExecutionSimulator()
    order = Order("limit1", "600438", "2025-01-02", "buy", quantity=100, limit_price=9.5)

    pending = sim.execute_order(order, _bar(low=9.8, high=10.5), cash=10_000, config=cfg)
    expired = sim.execute_order(order, _bar("2025-01-03", low=9.8, high=10.5), cash=10_000, config=cfg)
    touched = sim.execute_order(Order("limit2", "600438", "2025-01-02", "buy", quantity=100, limit_price=10.0), _bar(low=9.8, high=10.5, open=9.9), cash=10_000, config=cfg)
    sell = sim.execute_order(Order("limit3", "600438", "2025-01-02", "sell", quantity=100, limit_price=10.1), _bar(low=9.8, high=10.5, open=10.2), cash=0, position=Position("600438", quantity=100, available_quantity=100), config=cfg)

    assert pending.status == "pending"
    assert expired.status == "expired"
    assert touched.status == "filled"
    assert touched.fill.price <= 10.0
    assert sell.status == "filled"
    assert sell.fill.price >= 10.1


def test_a_share_rules_block_limits_t1_and_lots():
    sim = ExecutionSimulator()
    cfg = BacktestConfig(t_plus_one=True)
    order = Order("o1", "600438", "2025-01-01", "buy", quantity=100, signal_date="2025-01-01")
    assert sim.execute_order(order, _bar("2025-01-01"), cash=10_000, config=cfg).status == "blocked"
    assert sim.execute_order(Order("o2", "600438", "2025-01-02", "buy", quantity=100, signal_date="2025-01-01"), _bar(change_pct=10.0), cash=10_000, config=cfg).status == "blocked"
    assert sim.execute_order(Order("o3", "300750", "2025-01-02", "buy", quantity=150, signal_date="2025-01-01"), _bar(change_pct=19.6), cash=10_000, config=cfg).status == "blocked"


def test_rebalance_quality_exit_snapshot_and_metrics():
    cfg = BacktestConfig(max_positions=2, min_trade_amount=500, t_plus_one=True, stop_loss_pct=5, take_profit_pct=12)
    positions = {"600438": Position("600438", quantity=1000, available_quantity=1000, avg_cost=10, last_price=12, market_value=12_000)}
    plan = RebalanceEngine().generate_orders(date="2025-01-10", equity=100_000, cash=30_000, positions=positions, target_weights={"600438": 0.05, "300750": 0.2}, prices={"600438": 12, "300750": 20}, config=cfg)
    assert plan.orders and plan.orders[0].side == "sell"

    good, attr = StrategyQualityFilter().apply([StrategySignal("300750", "2025-01-10", "buy", score=70, features={"amount": 80_000_000, "market_env": "bull"})])
    bad, bad_attr = StrategyQualityFilter().apply([StrategySignal("600438", "2025-01-10", "buy", score=70, risk_flags=["退市风险"])])
    assert good and attr["passed"] == 1
    assert not bad and bad_attr["blocked_count"] == 1

    pos = Position("600438", quantity=100, available_quantity=100, avg_cost=10, last_price=10, highest_price=12)
    exit_decision = ExitPolicy().evaluate(pos, _bar(close=9.3, ma20=10), cfg)
    assert exit_decision.should_exit is True

    snapshots = HistoricalScreenerSnapshotBuilder().build("600438", _bars(80))
    assert snapshots[-1]["date"] <= _bars(80)[-1]["date"]
    assert "final_backtest_score" in snapshots[-1]

    metrics = calculate_metrics(
        [{"equity": 100_000}, {"equity": 105_000}, {"equity": 102_000}],
        trades=[{"pnl": 5000, "entry_signal_score": 70, "exit_policy": "target_profit", "pnl_pct": 5, "max_favorable_excursion_pct": 7}, {"pnl": -3000, "entry_signal_score": 62, "exit_policy": "fixed_stop_loss", "pnl_pct": -3, "max_adverse_excursion_pct": -4}],
    )
    assert "expectancy" in metrics
    assert metrics["max_consecutive_losses"] == 1
    assert "60-70" in metrics["signal_precision_buckets"]


def test_walk_forward_v320_objective_and_paper_gateway():
    bars = _bars(120)
    wf = WalkForwardValidator().run({"600438": bars}, BacktestConfig(symbols=["600438"], warmup_bars=10, volume_limit_pct=1), train_size=50, test_size=20, objective="composite_score")
    assert wf["objective"] == "composite_score"
    assert "overfit_warnings" in wf

    gateway = PaperTradingGateway()
    accepted = gateway.submit_signal(TradingSignal("300750", "buy", quantity=100, price=20, score=70, reason="unit"))
    rejected = gateway.submit_signal(TradingSignal("300750", "buy", quantity=10_000, price=20, score=40, reason="too large"))
    assert accepted["order"] is not None
    assert rejected["risk"]["allowed"] is False
    assert gateway.audit.list()
