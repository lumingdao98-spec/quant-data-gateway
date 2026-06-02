from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from .market_state_engine import MarketState
from .stock_classifier import StockProfile


@dataclass(slots=True)
class StrategySuitabilityResult:
    symbol: str
    strategy_family: str
    horizon: str
    risk_budget_hint: float
    confidence: float
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StrategySuitabilityEngine:
    """Map market state and stock profile into a strategy family."""

    def evaluate(
        self,
        symbol: str,
        asof_time: datetime | str,
        market_state: MarketState | dict[str, Any],
        stock_profile: StockProfile | dict[str, Any],
        factor_bundle: Any | None = None,
        event_bundle: Any | None = None,
    ) -> StrategySuitabilityResult:
        market = market_state if isinstance(market_state, MarketState) else _market_from_dict(market_state)
        profile = stock_profile if isinstance(stock_profile, StockProfile) else _profile_from_dict(symbol, stock_profile)
        factor_score = _extract_score(factor_bundle)
        event_risk = _event_risk(event_bundle)
        reasons: list[str] = []
        warnings: list[str] = []
        family = "avoid"
        horizon = "none"
        risk_budget = 0.0
        confidence = 0.45

        if event_risk >= 70:
            warnings.append("事件/公告风险过高，默认避开")
        elif profile.is_etf:
            family, horizon, risk_budget, confidence = "etf_allocation", "monthly", 0.012, 0.72
            reasons.append("ETF/基金更适合配置与再平衡")
        elif profile.is_compounder and market.market_regime in {"trend_up", "range"}:
            family, horizon, risk_budget, confidence = "long_term_compounder", "quarterly", 0.018, 0.70
            reasons.append("质量和趋势未破坏，偏长期复利/趋势跟随")
        elif profile.is_high_beta and market.risk_on_off == "risk_on" and factor_score >= 58:
            family, horizon, risk_budget, confidence = "short_term_momentum", "short_term", 0.010, 0.66
            reasons.append("高波动且市场风险偏好尚可，适合短线动量")
        elif profile.is_range_bound:
            family, horizon, risk_budget, confidence = "swing_reversion", "swing", 0.012, 0.62
            reasons.append("区间波动特征明显，适合波段/均值回归")
        elif profile.is_core_asset and market.risk_on_off != "risk_off":
            family, horizon, risk_budget, confidence = "dca_accumulate", "dca", 0.008, 0.58
            reasons.append("核心资产但趋势证据不足，适合定投观察")
        else:
            warnings.append("策略适配证据不足，默认避开或等待")

        if market.risk_on_off == "risk_off" and family not in {"avoid", "dca_accumulate"}:
            risk_budget *= 0.55
            warnings.append("市场风险偏好偏弱，风险预算降权")
        if not reasons and family != "avoid":
            reasons.append("由市场状态和股票画像联合适配")
        return StrategySuitabilityResult(
            symbol=symbol,
            strategy_family=family,
            horizon=horizon,
            risk_budget_hint=round(risk_budget, 6),
            confidence=round(confidence, 4),
            reasons=reasons,
            warnings=warnings,
        )


def evaluate_strategy_suitability(
    symbol: str,
    asof_time: datetime,
    market_state: MarketState,
    stock_profile: StockProfile,
    factor_bundle: Any,
    event_bundle: Any,
) -> StrategySuitabilityResult:
    return StrategySuitabilityEngine().evaluate(symbol, asof_time, market_state, stock_profile, factor_bundle, event_bundle)


def _extract_score(bundle: Any) -> float:
    if hasattr(bundle, "score"):
        return float(getattr(bundle, "score") or 0.0)
    if isinstance(bundle, dict):
        return float(bundle.get("score") or bundle.get("final_score") or 0.0)
    return 50.0


def _event_risk(bundle: Any) -> float:
    if isinstance(bundle, dict):
        return float(bundle.get("risk_score") or bundle.get("event_risk") or 0.0)
    if isinstance(bundle, list):
        text = " ".join(str(x) for x in bundle)
        return 80.0 if any(k in text for k in ["立案", "退市", "处罚", "暴雷"]) else 20.0
    return 0.0


def _market_from_dict(data: dict[str, Any] | None) -> MarketState:
    data = data or {}
    return MarketState(
        asof_time=str(data.get("asof_time") or ""),
        market_regime=str(data.get("market_regime") or "range"),
        risk_on_off=str(data.get("risk_on_off") or "neutral"),
        liquidity_state=str(data.get("liquidity_state") or "normal"),
        sentiment_score=float(data.get("sentiment_score") or 50.0),
        trend_score=float(data.get("trend_score") or 50.0),
        breadth_score=float(data.get("breadth_score") or 50.0),
        liquidity_score=float(data.get("liquidity_score") or 50.0),
    )


def _profile_from_dict(symbol: str, data: dict[str, Any] | None) -> StockProfile:
    data = data or {}
    return StockProfile(symbol=symbol, **{k: v for k, v in data.items() if k in StockProfile.__dataclass_fields__ and k != "symbol"})
