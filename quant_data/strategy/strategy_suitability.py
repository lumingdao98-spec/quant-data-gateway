from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .stock_classifier import StockProfileV323
from .strategy_family import STRATEGY_FAMILIES


@dataclass(slots=True)
class StrategySuitabilityDecision:
    symbol: str
    strategy_family: str
    stock_type: str
    can_auto_trade: bool
    risk_budget_hint: float
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommended_horizon: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StrategySuitabilityV323:
    def evaluate(
        self,
        profile: StockProfileV323 | dict[str, Any],
        *,
        score: float = 50.0,
        market_state: dict[str, Any] | None = None,
        data_quality_score: float = 50.0,
    ) -> StrategySuitabilityDecision:
        p = profile if isinstance(profile, StockProfileV323) else StockProfileV323(**profile)
        market_state = market_state or {}
        warnings: list[str] = []
        reasons: list[str] = []
        family = "avoid"
        risk_budget = 0.0
        if p.risk_flags:
            warnings.extend(p.risk_flags)
            reasons.append("高风险标的默认规避")
        elif data_quality_score < 45:
            warnings.append("数据不足：只观察，不自动交易")
            family = "avoid"
        elif p.stock_type == "etf_index":
            family = "dca" if score < 62 else "core_satellite"
            risk_budget = 0.008
            reasons.append("ETF/指数按配置或核心-卫星处理")
        elif p.stock_type == "long_term_compounder":
            family = "long_term"
            risk_budget = 0.016
            reasons.append("优质成长类不使用短线小止损作为主策略")
        elif p.stock_type in {"short_theme", "cyclical"}:
            family = "short_term" if score >= 66 else "swing"
            risk_budget = 0.009 if family == "short_term" else 0.012
            reasons.append("题材/周期按短线或波段处理，避免长线重仓")
        elif p.stock_type == "dividend_low_vol":
            family = "core_satellite"
            risk_budget = 0.012
            reasons.append("低波红利适合核心仓加卫星增强")
        elif p.stock_type == "turnaround":
            family = "event_driven"
            risk_budget = 0.008
            reasons.append("困境反转需事件驱动和严格退出")
        else:
            family = "swing" if score >= 58 else "avoid"
            risk_budget = 0.01 if family != "avoid" else 0.0
            reasons.append("画像不足，按波段观察或规避")
        if str(market_state.get("risk_on_off") or "").lower() == "risk_off" and family != "avoid":
            risk_budget *= 0.55
            warnings.append("大盘风险偏弱，风险预算降权")
        spec = STRATEGY_FAMILIES.get(family, STRATEGY_FAMILIES["avoid"])
        return StrategySuitabilityDecision(
            symbol=p.symbol,
            strategy_family=family,
            stock_type=p.stock_type,
            can_auto_trade=family != "avoid" and data_quality_score >= 45 and not p.risk_flags,
            risk_budget_hint=round(risk_budget, 6),
            reasons=reasons,
            warnings=warnings,
            recommended_horizon=spec.horizon,
        )
