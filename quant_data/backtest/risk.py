from __future__ import annotations

import math
from statistics import mean, pstdev
from typing import Any

from .models import Fill, Trade


def max_drawdown(equity: list[float]) -> dict[str, Any]:
    if not equity:
        return {"max_drawdown": 0.0, "start_index": 0, "end_index": 0, "recovered_index": None}
    peak = equity[0]
    peak_index = 0
    best = 0.0
    start = end = 0
    for idx, value in enumerate(equity):
        if value > peak:
            peak = value
            peak_index = idx
        dd = value / peak - 1 if peak else 0.0
        if dd < best:
            best = dd
            start = peak_index
            end = idx
    recovered = None
    if best < 0:
        target = equity[start]
        for idx in range(end + 1, len(equity)):
            if equity[idx] >= target:
                recovered = idx
                break
    return {"max_drawdown": best, "start_index": start, "end_index": end, "recovered_index": recovered}


def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def calculate_metrics(
    equity_curve: list[dict[str, Any]],
    trades: list[Trade] | list[dict[str, Any]] | None = None,
    fills: list[Fill] | list[dict[str, Any]] | None = None,
    benchmark_curve: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    trades = trades or []
    fills = fills or []
    values = [float(x.get("equity", 0.0)) for x in equity_curve if x.get("equity") is not None]
    if not values:
        return {
            "total_return": 0.0,
            "annualized_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe": 0.0,
            "sortino": 0.0,
            "calmar": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "turnover": 0.0,
            "total_cost": 0.0,
            "benchmark_return": 0.0,
            "excess_return": 0.0,
        }
    returns = [values[i] / values[i - 1] - 1 for i in range(1, len(values)) if values[i - 1]]
    total_return = values[-1] / values[0] - 1 if values[0] else 0.0
    periods = max(len(values) - 1, 1)
    annualized = (1 + total_return) ** (252 / periods) - 1 if total_return > -1 else -1.0
    dd = max_drawdown(values)
    vol = pstdev(returns) if len(returns) > 1 else 0.0
    avg = mean(returns) if returns else 0.0
    downside = [x for x in returns if x < 0]
    downside_vol = pstdev(downside) if len(downside) > 1 else 0.0
    sharpe = safe_div(avg, vol) * math.sqrt(252) if vol else 0.0
    sortino = safe_div(avg, downside_vol) * math.sqrt(252) if downside_vol else 0.0
    calmar = safe_div(annualized, abs(dd["max_drawdown"])) if dd["max_drawdown"] else 0.0
    trade_pnls = [_trade_value(t, "pnl") for t in trades]
    wins = [x for x in trade_pnls if x > 0]
    losses = [abs(x) for x in trade_pnls if x < 0]
    win_rate = safe_div(len(wins), len(trade_pnls))
    profit_factor = safe_div(sum(wins), sum(losses))
    total_cost = sum(_fill_cost(f) for f in fills)
    turnover = sum(abs(_fill_value(f)) for f in fills) / max(sum(values) / len(values), 1.0)
    benchmark_return = 0.0
    if benchmark_curve:
        bench_values = [float(x.get("close", x.get("equity", 0.0))) for x in benchmark_curve if x.get("close", x.get("equity", 0.0))]
        if len(bench_values) >= 2 and bench_values[0]:
            benchmark_return = bench_values[-1] / bench_values[0] - 1
    return {
        "total_return": round(total_return, 8),
        "total_return_pct": round(total_return * 100, 4),
        "annualized_return": round(annualized, 8),
        "annualized_return_pct": round(annualized * 100, 4),
        "max_drawdown": round(dd["max_drawdown"], 8),
        "max_drawdown_pct": round(dd["max_drawdown"] * 100, 4),
        "drawdown_start_index": dd["start_index"],
        "drawdown_end_index": dd["end_index"],
        "drawdown_recovered_index": dd["recovered_index"],
        "sharpe": round(sharpe, 4),
        "sortino": round(sortino, 4),
        "calmar": round(calmar, 4),
        "win_rate": round(win_rate, 8),
        "win_rate_pct": round(win_rate * 100, 4),
        "trade_count": len(trade_pnls),
        "profit_factor": round(profit_factor, 4),
        "turnover": round(turnover, 8),
        "total_cost": round(total_cost, 6),
        "benchmark_return": round(benchmark_return, 8),
        "benchmark_return_pct": round(benchmark_return * 100, 4),
        "excess_return": round(total_return - benchmark_return, 8),
        "excess_return_pct": round((total_return - benchmark_return) * 100, 4),
    }


def _trade_value(trade: Trade | dict[str, Any], key: str) -> float:
    if isinstance(trade, dict):
        return float(trade.get(key, 0.0) or 0.0)
    return float(getattr(trade, key, 0.0) or 0.0)


def _fill_value(fill: Fill | dict[str, Any]) -> float:
    if isinstance(fill, dict):
        return float(fill.get("gross_amount", 0.0) or 0.0)
    return float(getattr(fill, "gross_amount", 0.0) or 0.0)


def _fill_cost(fill: Fill | dict[str, Any]) -> float:
    if isinstance(fill, dict):
        return float(fill.get("total_cost", 0.0) or 0.0) or sum(float(fill.get(k, 0.0) or 0.0) for k in ("commission", "stamp_tax", "transfer_fee", "slippage_cost"))
    return float(fill.total_cost)
