from datetime import datetime, timedelta

from quant_data.backtest.money_management import MoneyManager
from quant_data.backtest.position_sizing import PositionSizer, PositionSizingConfig, PositionSizingRequest
from quant_data.backtest.strategy_horizon import StrategyHorizonConfig
from quant_data.trading.anomaly_guard import AnomalyGuard
from quant_data.trading.data_freshness import DataFreshnessGuard
from quant_data.trading.signal_fusion import SignalFusionEngine


def test_position_sizing_modes_cover_caps_and_loss_streak():
    req = PositionSizingRequest(symbol="300750", price=100, equity=100_000, cash=80_000, score=80, market_score=35)
    fixed = PositionSizer(PositionSizingConfig(sizing_mode="fixed_percent", max_single_position_pct=0.2)).size(req)
    weighted = PositionSizer(PositionSizingConfig(sizing_mode="score_weighted", max_single_position_pct=0.2)).size(req)
    atr = PositionSizer(PositionSizingConfig(sizing_mode="atr_risk", risk_per_trade_pct=0.02)).size(
        PositionSizingRequest(symbol="300750", price=100, equity=100_000, cash=80_000, atr=5, score=70)
    )
    kelly = PositionSizer(PositionSizingConfig(sizing_mode="fractional_kelly", kelly_fraction=0.25, max_single_position_pct=0.1)).size(
        PositionSizingRequest(symbol="300750", price=100, equity=100_000, cash=80_000, win_rate=0.7, payoff_ratio=2)
    )
    reduced = PositionSizer(PositionSizingConfig(reduce_after_loss_streak=2, risk_per_trade_pct=0.02)).size(
        PositionSizingRequest(symbol="300750", price=100, equity=100_000, cash=80_000, score=70, loss_streak=2)
    )

    assert fixed.target_weight <= 0.2
    assert weighted.target_weight < fixed.target_weight
    assert atr.target_weight <= 0.25
    assert kelly.target_weight <= 0.1
    assert reduced.risk_per_trade_pct == 0.01


def test_dca_pyramid_and_non_compound_equity_base():
    dca = PositionSizer(PositionSizingConfig(sizing_mode="dca", dca_amount=2000)).size(
        PositionSizingRequest(symbol="510300", price=5, equity=120_000, cash=20_000, valuation_level="low")
    )
    pyramid = PositionSizer(PositionSizingConfig(sizing_mode="pyramid", pyramid_step_pct=0.05, pyramid_max_adds=3)).size(
        PositionSizingRequest(symbol="300750", price=100, equity=100_000, cash=50_000, current_weight=0.1, current_position_value=10_000, unrealized_pct=0.08)
    )
    non_compound = PositionSizer(PositionSizingConfig(sizing_mode="fixed_percent", compound_returns=False, initial_cash=100_000)).size(
        PositionSizingRequest(symbol="300750", price=100, equity=150_000, cash=100_000, signal_target_weight=0.2)
    )

    assert dca.order_value >= 3000
    assert pyramid.target_weight > 0.1
    assert non_compound.target_value <= 25_000


def test_money_manager_tracks_reinvestment_and_ledger():
    mgr = MoneyManager(initial_cash=100_000, compound_returns=True, cash_reserve_pct=0.01)
    mgr.apply_buy(20_000, fee=10, slippage=5, date="2026-01-01", reason="buy signal")
    mgr.mark_to_market(24_000, unrealized_pnl=4000)
    before = mgr.snapshot()
    mgr.apply_sell(24_000, realized_pnl=3990, fee=12, date="2026-01-05", reason="sell signal")
    after = mgr.snapshot()

    assert before.equity > 100_000
    assert after.realized_pnl == 3990
    assert after.reinvestable_cash > 100_000
    assert len(mgr.ledger_dicts()) == 2
    assert mgr.ledger_dicts()[0]["action"] == "buy"
    assert mgr.ledger_dicts()[1]["action"] == "sell"


def test_strategy_horizon_signal_fusion_anomaly_and_freshness():
    short_rules = StrategyHorizonConfig(horizon="short_term").resolved_rules()
    dca_rules = StrategyHorizonConfig(horizon="dca").resolved_rules()
    anomaly = AnomalyGuard().check({"high_position_pct": 90, "volume_ratio": 3, "change_pct": 0.2})
    stale = DataFreshnessGuard().check(
        {"quote": datetime.now() - timedelta(minutes=1), "intraday": datetime.now(), "news": datetime.now(), "technical": datetime.now(), "company_profile": datetime.now()}
    )
    signal = SignalFusionEngine().fuse(
        symbol="300750",
        horizon="swing",
        fundamental_score=None,
        technical_score=78,
        information_score=62,
        market_score=55,
        anomaly_score=anomaly.anomaly_score,
        anomaly_action=anomaly.action_suggestion,
        evidence=["unit"],
        data_freshness=stale.to_dict(),
    )

    assert short_rules["max_holding_days"] <= 5
    assert dca_rules["allow_dca"] is True
    assert anomaly.anomaly_score > 0
    assert stale.action == "block"
    assert signal.missing_data
    assert signal.final_score >= 0
