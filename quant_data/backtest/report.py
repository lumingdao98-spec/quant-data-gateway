from __future__ import annotations

from typing import Any

from .models import DISCLAIMER, BacktestResult


def build_report(result: BacktestResult | dict[str, Any]) -> dict[str, Any]:
    data = result.to_dict() if hasattr(result, "to_dict") else dict(result)
    metrics = data.get("metrics", {})
    return {
        "run_id": data.get("run_id"),
        "title": "V3.19 交易回测报告",
        "summary": {
            "symbols": data.get("symbols", []),
            "strategy": (data.get("config") or {}).get("strategy"),
            "total_return_pct": metrics.get("total_return_pct", 0.0),
            "annualized_return_pct": metrics.get("annualized_return_pct", 0.0),
            "max_drawdown_pct": metrics.get("max_drawdown_pct", 0.0),
            "sharpe": metrics.get("sharpe", 0.0),
            "trade_count": metrics.get("trade_count", 0),
        },
        "sections": [
            "数据口径：日线、复权口径、样本 warmup 与数据质量检查。",
            "信号口径：信号日只读取当日及历史数据，下一交易日按执行模型成交。",
            "成交口径：A 股 T+1、100 股整数手、涨跌停/停牌/成交量限制、手续费/印花税/过户费/滑点。",
            "风险口径：最大回撤、胜率、夏普、Sortino、Calmar、换手、成本、基准超额。",
        ],
        "warnings": data.get("warnings", []),
        "errors": data.get("errors", []),
        "disclaimer": data.get("disclaimer") or DISCLAIMER,
    }
