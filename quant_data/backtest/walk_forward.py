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
                    "warnings": [*is_result.warnings, *oos_result.warnings],
                }
            )
            start += test_size
        stable = sum(1 for w in windows if float(w["oos_metrics"].get("total_return", 0.0)) >= 0)
        stability_score = stable / len(windows) if windows else 0.0
        return {
            "windows": windows,
            "stability_score": round(stability_score, 4),
            "overfit_flag": bool(windows and stability_score < 0.5),
            "message": "滚动样本外验证完成" if windows else "样本不足，无法滚动验证",
        }
