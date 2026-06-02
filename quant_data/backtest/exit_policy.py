from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .data_loader import field_value, number
from .models import BacktestConfig, Position


@dataclass(slots=True)
class ExitDecision:
    should_exit: bool
    policy: str = ""
    reason: str = ""
    partial_pct: float = 1.0


class ExitPolicy:
    """Composable exit rules used by backtests and paper trading readiness checks."""

    def evaluate(
        self,
        position: Position,
        bar: Any,
        config: BacktestConfig,
        *,
        score: float | None = None,
        bars_held: int = 0,
        behavior_risk_reversal: bool = False,
        sector_retreat: bool = False,
        thesis_broken: bool = False,
        anomaly_exit: bool = False,
        market_emergency: bool = False,
    ) -> ExitDecision:
        close = number(field_value(bar, "close"), position.last_price)
        if position.avg_cost <= 0 or close <= 0:
            return ExitDecision(False)
        pnl_pct = (close / position.avg_cost - 1) * 100
        from_high_pct = (close / max(position.highest_price or close, close) - 1) * 100
        atr_pct = number(field_value(bar, "atr_pct"), number(field_value(bar, "atr"), 0.0) / close * 100 if close else 0.0)
        ma20 = number(field_value(bar, "ma20"), 0.0)
        if market_emergency:
            return ExitDecision(True, "market_emergency_exit", "市场紧急风控退出")
        if anomaly_exit:
            return ExitDecision(True, "anomaly_exit", "异常事件/波动触发退出")
        if thesis_broken:
            return ExitDecision(True, "thesis_break_exit", "开仓逻辑失效")
        if config.stop_loss_pct and pnl_pct <= -abs(config.stop_loss_pct):
            return ExitDecision(True, "fixed_stop_loss", f"固定止损 {pnl_pct:.2f}%")
        if config.atr_stop_multiplier and atr_pct and pnl_pct <= -abs(config.atr_stop_multiplier * atr_pct):
            return ExitDecision(True, "atr_trailing_stop", f"ATR跟踪止损 {pnl_pct:.2f}% / ATR {atr_pct:.2f}%")
        if config.trailing_stop_pct and from_high_pct <= -abs(config.trailing_stop_pct):
            return ExitDecision(True, "atr_trailing_stop", f"跟踪止损 {from_high_pct:.2f}%")
        if ma20 and close < ma20:
            return ExitDecision(True, "thesis_break_exit", "跌破MA20")
        if behavior_risk_reversal:
            return ExitDecision(True, "anomaly_exit", "行为风险反转")
        if config.max_holding_days and bars_held >= config.max_holding_days and pnl_pct <= 0:
            return ExitDecision(True, "time_stop", "持有超时且无盈利")
        if config.take_profit_pct and pnl_pct >= abs(config.take_profit_pct):
            return ExitDecision(True, "fixed_take_profit", f"固定止盈 {pnl_pct:.2f}%")
        if config.partial_take_profit_pct and pnl_pct >= abs(config.partial_take_profit_pct):
            return ExitDecision(True, "staged_take_profit", f"分批止盈 {pnl_pct:.2f}%", partial_pct=0.5)
        if score is not None and score < config.sell_score:
            return ExitDecision(True, "score_decay_exit", f"评分跌破卖出线 {score:.1f} < {config.sell_score:.1f}")
        if sector_retreat:
            return ExitDecision(True, "thesis_break_exit", "板块强度回落")
        return ExitDecision(False)

    @staticmethod
    def supported_policies() -> list[str]:
        return [
            "fixed_stop_loss",
            "fixed_take_profit",
            "atr_trailing_stop",
            "time_stop",
            "thesis_break_exit",
            "score_decay_exit",
            "anomaly_exit",
            "staged_take_profit",
            "market_emergency_exit",
        ]
