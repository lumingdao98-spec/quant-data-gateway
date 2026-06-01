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

__all__ = [
    "BacktestConfig",
    "BacktestEngine",
    "BacktestEngineV320",
    "BacktestResult",
    "Fill",
    "Order",
    "PortfolioState",
    "Position",
    "StrategySignal",
    "Trade",
]
