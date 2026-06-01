from __future__ import annotations

from dataclasses import replace
from typing import Any

from .engine import BacktestEngine
from .models import BacktestConfig


class WalkForwardValidator:
    def __init__(self, engine: BacktestEngine | None = None) -> None:
        self.engine = engine or BacktestEngine()

    def run(
        self,
        bars_by_symbol: dict[str, list[Any]],
        config: BacktestConfig,
        *,
        train_size: int = 180,
        test_size: int = 60,
        expanding: bool = True,
        objective: str = "composite_score",
    ) -> dict[str, Any]:
        first_symbol = next(iter(bars_by_symbol), None)
        length = len(bars_by_symbol[first_symbol]) if first_symbol else 0
        windows = []
        start = 0
        while start + train_size + test_size <= length:
            train_start = 0 if expanding else start
            train_end = start + train_size
            test_end = train_end + test_size
            train_data = {s: rows[train_start:train_end] for s, rows in bars_by_symbol.items()}
            test_data = {s: rows[train_end:test_end] for s, rows in bars_by_symbol.items()}
            is_result = self.engine.run(replace(config, run_id=None), market_data=train_data)
            oos_result = self.engine.run(replace(config, run_id=None), market_data=test_data)
            windows.append(
                {
                    "train": [train_start, train_end],
                    "test": [train_end, test_end],
                    "is_metrics": is_result.metrics,
                    "oos_metrics": oos_result.metrics,
                    "degradation": round(float(is_result.metrics.get("sharpe", 0.0)) - float(oos_result.metrics.get("sharpe", 0.0)), 4),
                    "objective": objective,
                    "is_objective": self._objective(is_result.metrics, objective),
                    "oos_objective": self._objective(oos_result.metrics, objective),
                    "oos_win_rate": oos_result.metrics.get("win_rate"),
                    "oos_max_drawdown": oos_result.metrics.get("max_drawdown"),
                    "warnings": [*is_result.warnings, *oos_result.warnings],
                }
            )
            start += test_size
        stable = sum(1 for w in windows if float(w["oos_metrics"].get("total_return", 0.0)) >= 0)
        stability_score = stable / len(windows) if windows else 0.0
        overfit_warnings = []
        if windows and stability_score < 0.5:
            overfit_warnings.append("样本外盈利窗口少于一半，存在过拟合风险")
        if windows and any(float(w["oos_metrics"].get("max_drawdown", 0.0) or 0.0) < -0.25 for w in windows):
            overfit_warnings.append("样本外出现超过25%回撤窗口")
        return {
            "windows": windows,
            "stability_score": round(stability_score, 4),
            "overfit_flag": bool(overfit_warnings),
            "overfit_warnings": overfit_warnings,
            "objective": objective,
            "message": "滚动样本外验证完成" if windows else "样本不足，无法滚动验证",
        }

    @staticmethod
    def _objective(metrics: dict[str, Any], objective: str) -> float:
        if objective == "composite_score":
            ret = float(metrics.get("annualized_return", metrics.get("total_return", 0.0)) or 0.0)
            sharpe = float(metrics.get("sharpe", 0.0) or 0.0)
            calmar = float(metrics.get("calmar", 0.0) or 0.0)
            dd = abs(float(metrics.get("max_drawdown", 0.0) or 0.0))
            expectancy = float(metrics.get("expectancy_pct_of_start", 0.0) or 0.0) / 100
            win = float(metrics.get("win_rate", 0.0) or 0.0)
            return round(ret * 0.28 + sharpe * 0.18 + calmar * 0.18 + expectancy * 0.18 + win * 0.10 - dd * 0.22, 6)
        return round(float(metrics.get(objective, metrics.get(f"{objective}_pct", 0.0)) or 0.0), 6)
