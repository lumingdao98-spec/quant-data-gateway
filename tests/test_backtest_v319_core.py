from __future__ import annotations

from pathlib import Path

from quant_data.backtest.data_loader import BacktestDataLoader
from quant_data.backtest.engine import BacktestEngine
from quant_data.backtest.execution import ExecutionSimulator
from quant_data.backtest.models import BacktestConfig, Order, Position, StrategySignal
from quant_data.backtest.optimizer import ParameterOptimizer
from quant_data.backtest.paper_broker import PaperBroker
from quant_data.backtest.portfolio import PortfolioManager
from quant_data.backtest.risk import calculate_metrics, max_drawdown
from quant_data.backtest.signal_adapter import SignalAdapter
from quant_data.backtest.storage import BacktestStorage
from quant_data.backtest.walk_forward import WalkForwardValidator


def _bars(count: int = 90, start: float = 10.0) -> list[dict]:
    rows = []
    for i in range(count):
        price = start + i * 0.08
        rows.append(
            {
                "symbol": "600438",
                "date": f"2025-01-{(i % 28) + 1:02d}" if i < 28 else f"2025-02-{((i - 28) % 28) + 1:02d}" if i < 56 else f"2025-03-{((i - 56) % 28) + 1:02d}",
                "open": round(price * 0.995, 4),
                "high": round(price * 1.02, 4),
                "low": round(price * 0.98, 4),
                "close": round(price, 4),
                "volume": 2_000_000 + i * 1000,
                "amount": price * (2_000_000 + i * 1000),
            }
        )
    return rows


def test_data_quality_and_no_lookahead_checks():
    cfg = BacktestConfig(warmup_bars=20)
    rows = _bars(25)
    rows.append({**rows[-1], "date": rows[-1]["date"], "volume": 0, "high": 1, "low": 3})
    report = BacktestDataLoader().quality_report(rows, cfg, symbol="600438")

    assert report["duplicate_dates"]
    assert report["zero_volume_dates"]
    assert report["ohlc_anomalies"]
    assert "pit_note" in report
    assert BacktestDataLoader.assert_no_lookahead("2025-01-10", "2025-01-11")[0] is True
    assert BacktestDataLoader.assert_no_lookahead("2025-01-10", "2025-01-10")[0] is False


def test_signal_adapter_screener_factor_and_event_filter():
    cfg = BacktestConfig(buy_score=60, max_positions=2, screener_snapshot_id="snap-test")
    rows = [
        {"symbol": "600438", "score": 75, "grade": "B", "amount": 10},
        {"symbol": "300750", "score": 72, "grade": "C", "amount": 9},
        {"symbol": "000001", "score": 90, "grade": "D 剔除", "amount": 100},
    ]
    adapter = SignalAdapter()
    signals = adapter.score_rank_rebalance(rows, "2025-01-10", cfg)

    assert [s.symbol for s in signals] == ["600438", "300750"]
    assert signals[0].snapshot_id == "snap-test"
    factor = adapter.factor_rule_strategy(
        [{"symbol": "600438", "date": "2025-01-10", "close": 12, "ma20": 10, "ma60": 9, "rsi14": 55, "volume_ratio": 2.0}],
        cfg,
    )
    assert factor and factor[0].action == "buy"
    filtered = adapter.event_risk_filter(signals, {"600438": [{"title": "控股股东减持", "severity": "high"}]})
    assert filtered[0].action == "avoid"


def test_execution_a_share_costs_lots_t1_and_volume_cap():
    cfg = BacktestConfig(lot_size=100, volume_limit_pct=0.1, slippage_bps=10, t_plus_one=True)
    simulator = ExecutionSimulator()
    order = Order("o1", "600438", "2025-01-11", "buy", quantity=1234, signal_date="2025-01-10")
    decision = simulator.execute_order(order, {"date": "2025-01-11", "open": 10, "high": 10.5, "low": 9.8, "close": 10.2, "volume": 10}, cash=100_000, config=cfg)

    assert decision.status == "partial"
    assert decision.fill is not None
    assert decision.fill.quantity == 100
    assert decision.fill.commission >= cfg.min_commission
    blocked = simulator.execute_order(order, {"date": "2025-01-10", "open": 10, "high": 10, "low": 10, "close": 10, "volume": 100}, cash=100_000, config=cfg)
    assert blocked.status == "blocked"
    limit_buy = simulator.execute_order(order, {"date": "2025-01-11", "open": 11, "high": 11, "low": 11, "close": 11, "volume": 1000, "change_pct": 10}, cash=100_000, config=cfg)
    assert limit_buy.status == "blocked"


def test_portfolio_state_position_sizing_and_stops():
    cfg = BacktestConfig(max_positions=2, max_single_position_pct=0.3, stop_loss_pct=5, t_plus_one=False)
    pm = PortfolioManager(cfg)
    weights = pm.allocate_weights(
        [
            StrategySignal("a", "2025-01-01", "buy", score=90),
            StrategySignal("b", "2025-01-01", "buy", score=70),
            StrategySignal("c", "2025-01-01", "buy", score=60),
        ]
    )
    assert set(weights) == {"a", "b"}
    assert all(v <= 0.3 for v in weights.values())
    pm.positions["a"] = Position(symbol="a", quantity=1000, available_quantity=1000, avg_cost=10, last_price=10, highest_price=11)
    state = pm.mark_to_market({"a": {"close": 9}}, "2025-01-02")
    assert state.equity > 0
    stops = pm.stop_orders("2025-01-02", {"a": {"close": 9}})
    assert stops and stops[0].side == "sell"


def test_risk_metrics_are_safe_and_include_benchmark():
    empty = calculate_metrics([])
    assert empty["sharpe"] == 0.0
    dd = max_drawdown([100, 120, 90, 130])
    assert round(dd["max_drawdown"], 4) == -0.25
    metrics = calculate_metrics(
        [{"equity": 100}, {"equity": 110}, {"equity": 105}, {"equity": 120}],
        trades=[{"pnl": 10}, {"pnl": -2}],
        fills=[{"gross_amount": 1000, "commission": 5, "stamp_tax": 1, "transfer_fee": 0.1, "slippage_cost": 0.5}],
        benchmark_curve=[{"close": 100}, {"close": 115}],
    )
    assert metrics["total_return_pct"] == 20
    assert metrics["benchmark_return_pct"] == 15
    assert metrics["total_cost"] > 0


def test_engine_optimizer_walk_forward_storage_and_paper(tmp_path: Path):
    bars = _bars(100)
    cfg = BacktestConfig(symbols=["600438"], warmup_bars=10, buy_score=58, sell_score=45, max_positions=1, volume_limit_pct=1.0)
    engine = BacktestEngine()
    result = engine.run(cfg, market_data={"600438": bars})
    assert result.run_id
    assert result.metrics["total_return"] > -1
    assert result.data_quality["no_lookahead"] is True

    optimizer = ParameterOptimizer(engine)
    ranked = optimizer.grid_search(cfg, {"buy_score": [55, 60]}, market_data={"600438": bars}, objective="total_return")
    assert len(ranked) == 2
    assert ranked[0]["score"] >= ranked[-1]["score"]

    wf = WalkForwardValidator(engine).run({"600438": bars}, cfg, train_size=40, test_size=20)
    assert "stability_score" in wf

    storage = BacktestStorage(tmp_path)
    run_id = storage.save(result)
    assert storage.load(run_id)["run_id"] == run_id
    assert storage.list_runs()
    assert storage.export_trades_csv(run_id).exists()
    assert storage.delete(run_id) is True

    broker = PaperBroker(cfg)
    paper_order = broker.receive_signal(StrategySignal("600438", "2025-01-01", "buy", score=80, target_weight=0.2, reason="unit"))
    assert paper_order is not None
    fill = broker.simulate_fill(paper_order, {"date": "2025-01-02", "open": 10, "high": 10.5, "low": 9.8, "close": 10.2, "volume": 1_000_000})
    assert fill is not None
    assert "不构成投资建议" in broker.snapshot()["disclaimer"]
