"""Backtest and paper-trading foundation for Quant Data Gateway V3.20."""

from .engine import BacktestEngine, BacktestEngineV320
from .models import (
    BacktestConfig,
    BacktestResult,
    Fill,
    Order,
    PortfolioState,
    Position,
    StrategySignal,
    Trade,
)
from .money_management import AccountSnapshot, CashLedgerEntry, MoneyManager
from .position_sizing import PositionSizingConfig, PositionSizingDecision, PositionSizingRequest, PositionSizer
from .strategy_horizon import StrategyHorizonConfig

__all__ = [
    "AccountSnapshot",
    "BacktestConfig",
    "BacktestEngine",
    "BacktestEngineV320",
    "BacktestResult",
    "CashLedgerEntry",
    "Fill",
    "MoneyManager",
    "Order",
    "PortfolioState",
    "Position",
    "PositionSizer",
    "PositionSizingConfig",
    "PositionSizingDecision",
    "PositionSizingRequest",
    "StrategyHorizonConfig",
    "StrategySignal",
    "Trade",
]
