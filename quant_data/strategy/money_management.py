from __future__ import annotations

from typing import Any

from quant_data.backtest.money_management import CashPolicyResult, MoneyManagementPolicy, MoneyManager


class MoneyManagementV323:
    def __init__(self, initial_cash: float = 100_000.0) -> None:
        self.manager = MoneyManager(initial_cash=initial_cash)

    def policy(self, mode: str = "full_compounding", **kwargs: Any) -> CashPolicyResult:
        return self.manager.cash_policy(MoneyManagementPolicy(mode=mode, **kwargs))
