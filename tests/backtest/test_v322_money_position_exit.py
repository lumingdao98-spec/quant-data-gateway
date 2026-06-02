from quant_data.backtest.exit_policy import ExitPolicy
from quant_data.backtest.money_management import MoneyManagementPolicy, MoneyManager
from quant_data.backtest.models import BacktestConfig, Position
from quant_data.backtest.position_sizing import size_position


def test_size_position_function_adapter_supports_document_aliases():
    decision = size_position(
        {"symbol": "300750", "final_score": 80, "target_weight": 0.2},
        {"cash": 80_000, "equity": 100_000, "target_positions": 4},
        {"stop_distance_pct": 0.08},
        {"symbol": "300750"},
        {"close": 100, "atr": 5},
        {"sizing_mode": "kelly_capped", "max_single_position_pct": 0.3},
    )

    data = decision.to_dict()
    assert data["sizing_mode"] == "kelly_capped"
    assert data["actual_weight"] <= 0.3
    assert "position_utilization" in data
    assert "cash_drag" in data


def test_money_management_policy_modes_change_deployable_cash():
    mgr = MoneyManager(initial_cash=100_000, compound_returns=True, cash_reserve_pct=0.02)
    mgr.apply_buy(30_000, fee=10)
    mgr.mark_to_market(40_000, unrealized_pnl=10_000)

    dca = mgr.cash_policy(MoneyManagementPolicy(mode="dca_schedule", dca_amount=2500))
    capped = mgr.cash_policy(MoneyManagementPolicy(mode="capped_compounding", cap_multiple=1.05))
    core = mgr.cash_policy(MoneyManagementPolicy(mode="core_satellite", core_cash_reserve_pct=0.30))

    assert dca.deployable_cash == 2500
    assert capped.deployable_cash <= mgr.available_cash
    assert core.reserved_cash >= mgr.reserved_cash
    assert 0 <= core.cash_drag <= 1


def test_exit_policy_exposes_required_v322_exit_reasons():
    supported = set(ExitPolicy.supported_policies())
    assert {"fixed_stop_loss", "fixed_take_profit", "atr_trailing_stop", "score_decay_exit", "market_emergency_exit"} <= supported

    position = Position("300750", quantity=100, avg_cost=100, last_price=100, highest_price=112)
    bar = {"close": 90, "atr_pct": 4, "ma20": 95}
    decision = ExitPolicy().evaluate(position, bar, BacktestConfig(stop_loss_pct=8))
    assert decision.should_exit is True
    assert decision.policy == "fixed_stop_loss"

    emergency = ExitPolicy().evaluate(position, {"close": 105}, BacktestConfig(), market_emergency=True)
    assert emergency.policy == "market_emergency_exit"
