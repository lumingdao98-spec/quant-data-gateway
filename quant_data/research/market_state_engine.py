from __future__ import annotations

from dataclasses import asdict, dataclass, field
from statistics import mean
from typing import Any


@dataclass(slots=True)
class MarketState:
    asof_time: str
    market_regime: str
    risk_on_off: str
    liquidity_state: str
    sentiment_score: float
    trend_score: float
    breadth_score: float
    liquidity_score: float
    source_refs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MarketStateEngine:
    """Compute a compact market-regime snapshot from point-in-time inputs."""

    def compute(self, inputs: dict[str, Any] | None = None, *, asof_time: str = "") -> MarketState:
        inputs = inputs or {}
        index_returns = _numbers(inputs.get("index_returns") or inputs.get("indices") or [])
        up_count = _num(inputs.get("up_count"))
        down_count = _num(inputs.get("down_count"))
        amount = _num(inputs.get("amount") or inputs.get("turnover_amount"))
        amount_ma = _num(inputs.get("amount_ma20") or inputs.get("turnover_amount_ma20"))
        northbound = _num(inputs.get("northbound_net"))
        source_refs = [str(x) for x in inputs.get("source_refs") or [] if str(x)]

        trend_score = _clip(50 + (mean(index_returns) if index_returns else _num(inputs.get("index_change_pct"))) * 5)
        breadth_total = up_count + down_count
        breadth_score = _clip(50 + ((up_count - down_count) / breadth_total * 50 if breadth_total else 0))
        liquidity_score = _clip(50 + ((amount / amount_ma - 1) * 35 if amount > 0 and amount_ma > 0 else 0) + min(max(northbound / 10_000_000_000, -1), 1) * 8)
        sentiment_score = _clip(trend_score * 0.42 + breadth_score * 0.34 + liquidity_score * 0.24)

        if sentiment_score >= 62 and trend_score >= 58:
            regime = "trend_up"
        elif sentiment_score <= 38 and trend_score <= 45:
            regime = "risk_off"
        elif liquidity_score < 35:
            regime = "liquidity_dry"
        else:
            regime = "range"
        risk = "risk_on" if sentiment_score >= 55 else "risk_off" if sentiment_score <= 42 else "neutral"
        liquidity = "ample" if liquidity_score >= 60 else "tight" if liquidity_score <= 38 else "normal"
        warnings = []
        if not index_returns and not inputs.get("index_change_pct"):
            warnings.append("缺少指数涨跌数据，市场状态按中性估算")
        return MarketState(
            asof_time=asof_time or str(inputs.get("asof_time") or ""),
            market_regime=regime,
            risk_on_off=risk,
            liquidity_state=liquidity,
            sentiment_score=round(sentiment_score, 4),
            trend_score=round(trend_score, 4),
            breadth_score=round(breadth_score, 4),
            liquidity_score=round(liquidity_score, 4),
            source_refs=source_refs,
            warnings=warnings,
        )


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _numbers(value: Any) -> list[float]:
    if isinstance(value, dict):
        value = value.values()
    if not isinstance(value, (list, tuple, set)):
        value = [value] if value not in (None, "") else []
    return [_num(x) for x in value if x not in (None, "")]


def _clip(value: float) -> float:
    return max(0.0, min(100.0, float(value)))
