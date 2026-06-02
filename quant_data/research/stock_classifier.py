from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class StockProfile:
    symbol: str
    security_type: str = "stock"
    exchange: str = ""
    board: str = ""
    is_etf: bool = False
    is_compounder: bool = False
    is_high_beta: bool = False
    is_range_bound: bool = False
    is_core_asset: bool = False
    liquidity_score: float = 50.0
    quality_score: float = 50.0
    volatility_pct: float = 0.0
    archetype_tags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StockClassifier:
    """Classify an A-share/ETF into strategy-relevant archetypes."""

    def classify(self, symbol: str, features: dict[str, Any] | None = None) -> StockProfile:
        features = features or {}
        symbol = str(symbol or features.get("symbol") or "").strip()
        security_type = str(features.get("security_type") or features.get("asset_type") or "").lower()
        name = str(features.get("name") or "")
        is_etf = security_type in {"etf", "fund"} or symbol.startswith(("51", "15", "16", "58")) or "ETF" in name.upper()
        volatility = _num(features.get("volatility_pct") or features.get("atr_pct"))
        roe = _num(features.get("roe") or features.get("roe_weighted"))
        cashflow_quality = _num(features.get("cashflow_quality"), 50.0)
        trend_score = _num(features.get("trend_score") or features.get("technical_score"), 50.0)
        liquidity_score = _score_liquidity(features)
        quality_score = _clip((roe * 2 if roe else 50.0) * 0.35 + cashflow_quality * 0.35 + trend_score * 0.30)
        tags: list[str] = []
        is_compounder = bool(features.get("is_compounder")) or (quality_score >= 62 and trend_score >= 55 and not is_etf)
        is_high_beta = volatility >= 6 or bool(features.get("high_beta"))
        pos60 = _num(features.get("pos60") or features.get("range_position"), 50.0)
        is_range_bound = 25 <= pos60 <= 75 and trend_score < 62
        is_core_asset = is_etf or is_compounder or bool(features.get("core_asset"))
        for flag, tag in [
            (is_etf, "ETF/基金"),
            (is_compounder, "长期复利候选"),
            (is_high_beta, "高波动"),
            (is_range_bound, "区间波段"),
            (is_core_asset, "核心资产观察"),
        ]:
            if flag:
                tags.append(tag)
        return StockProfile(
            symbol=symbol,
            security_type="etf" if is_etf else security_type or "stock",
            exchange=str(features.get("exchange") or ""),
            board=str(features.get("board") or ""),
            is_etf=is_etf,
            is_compounder=is_compounder,
            is_high_beta=is_high_beta,
            is_range_bound=is_range_bound,
            is_core_asset=is_core_asset,
            liquidity_score=round(liquidity_score, 4),
            quality_score=round(quality_score, 4),
            volatility_pct=round(volatility, 4),
            archetype_tags=tags,
            warnings=[] if symbol else ["缺少证券代码"],
        )


def _score_liquidity(features: dict[str, Any]) -> float:
    amount = _num(features.get("amount") or features.get("turnover_amount"))
    turnover = _num(features.get("turnover") or features.get("turnover_rate"))
    amount_score = 35 if amount <= 0 else min(85, 35 + amount / 100_000_000 * 18)
    turnover_score = min(85, 45 + turnover * 5)
    return _clip(amount_score * 0.6 + turnover_score * 0.4)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clip(value: float) -> float:
    return max(0.0, min(100.0, float(value)))
