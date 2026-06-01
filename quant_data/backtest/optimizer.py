from __future__ import annotations

import itertools
import random
from dataclasses import replace
from typing import Any

from .engine import BacktestEngine
from .models import BacktestConfig


class ParameterOptimizer:
    def __init__(self, engine: BacktestEngine | None = None) -> None:
        self.engine = engine or BacktestEngine()

    def grid_search(
        self,
        config: BacktestConfig,
        param_grid: dict[str, list[Any]],
        *,
        market_data: dict[str, list[Any]] | None = None,
        objective: str = "sharpe",
    ) -> list[dict[str, Any]]:
        keys = list(param_grid)
        runs: list[dict[str, Any]] = []
        for values in itertools.product(*(param_grid[k] for k in keys)):
            params = dict(zip(keys, values))
            cfg = replace(config, **params)
            result = self.engine.run(cfg, market_data=market_data)
            metric = self._objective_value(result.metrics, objective)
            runs.append({"params": params, "objective": objective, "score": metric, "metrics": result.metrics, "run_id": result.run_id})
        return sorted(runs, key=lambda x: x["score"], reverse=True)

    def random_search(
        self,
        config: BacktestConfig,
        param_grid: dict[str, list[Any]],
        n_iter: int = 10,
        *,
        market_data: dict[str, list[Any]] | None = None,
        objective: str = "sharpe",
    ) -> list[dict[str, Any]]:
        keys = list(param_grid)
        samples = []
        for _ in range(max(1, n_iter)):
            samples.append({k: random.choice(param_grid[k]) for k in keys})
        return self.grid_search(config, {f"sample_{i}": [v] for i, v in enumerate([])}, market_data=market_data) if False else self._run_samples(config, samples, market_data, objective)

    def _run_samples(self, config: BacktestConfig, samples: list[dict[str, Any]], market_data: dict[str, list[Any]] | None, objective: str) -> list[dict[str, Any]]:
        runs = []
        for params in samples:
            result = self.engine.run(replace(config, **params), market_data=market_data)
            runs.append({"params": params, "objective": objective, "score": self._objective_value(result.metrics, objective), "metrics": result.metrics, "run_id": result.run_id})
        return sorted(runs, key=lambda x: x["score"], reverse=True)

    @staticmethod
    def _objective_value(metrics: dict[str, Any], objective: str) -> float:
        if objective == "composite_score":
            ret = float(metrics.get("annualized_return", metrics.get("total_return", 0.0)) or 0.0)
            sharpe = float(metrics.get("sharpe", 0.0) or 0.0)
            calmar = float(metrics.get("calmar", 0.0) or 0.0)
            expectancy = float(metrics.get("expectancy_pct_of_start", 0.0) or 0.0) / 100
            dd = abs(float(metrics.get("max_drawdown", 0.0) or 0.0))
            win = float(metrics.get("win_rate", 0.0) or 0.0)
            return ret * 0.28 + sharpe * 0.18 + calmar * 0.18 + expectancy * 0.18 + win * 0.10 - dd * 0.22
        if objective in {"max_drawdown", "max_drawdown_pct"}:
            return -abs(float(metrics.get("max_drawdown", metrics.get("max_drawdown_pct", 0.0)) or 0.0))
        return float(metrics.get(objective, metrics.get(f"{objective}_pct", 0.0)) or 0.0)
