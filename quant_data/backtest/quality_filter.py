from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import StrategySignal


@dataclass(slots=True)
class QualityDecision:
    allowed: bool
    reason: str = ""
    tags: list[str] = field(default_factory=list)


class StrategyQualityFilter:
    """Pre-trade research filter for market/sector/technical/liquidity risks."""

    def apply(
        self,
        signals: list[StrategySignal],
        *,
        context: dict[str, Any] | None = None,
    ) -> tuple[list[StrategySignal], dict[str, Any]]:
        context = context or {}
        passed: list[StrategySignal] = []
        blocked: list[str] = []
        for signal in signals:
            decision = self.evaluate(signal, context)
            if decision.allowed:
                if decision.tags:
                    signal.risk_flags.extend(decision.tags)
                passed.append(signal)
            else:
                blocked.append(f"{signal.symbol}: {decision.reason}")
        return passed, {"passed": len(passed), "blocked_count": len(blocked), "blocked": blocked}

    def evaluate(self, signal: StrategySignal, context: dict[str, Any] | None = None) -> QualityDecision:
        context = context or {}
        features = dict(signal.features or {})
        market_env = str(context.get("market_env") or features.get("market_env") or "").lower()
        if signal.action == "buy" and market_env in {"panic", "bear", "weak"}:
            return QualityDecision(False, "大盘环境偏弱，过滤买入信号", ["market_weak"])
        risk_flags = [str(x) for x in signal.risk_flags or features.get("risk_flags") or []]
        if signal.action == "buy" and any(x in " ".join(risk_flags) for x in ["退市", "立案", "高风险", "暴雷"]):
            return QualityDecision(False, "行为/事件风险过高", ["behavior_risk"])
        amount = _num(features.get("amount", features.get("turnover_amount", 0.0)))
        if signal.action == "buy" and amount and amount < 30_000_000:
            return QualityDecision(False, "流动性不足，低于3000万成交额", ["low_liquidity"])
        resistance_dist = _num(features.get("resistance_dist_pct", 99.0), 99.0)
        support_dist = abs(_num(features.get("support_dist_pct", 99.0), 99.0))
        if signal.action == "buy" and resistance_dist < 3.0 and support_dist > 8.0:
            return QualityDecision(False, "压力位过近且支撑距离过远，风险收益不合格", ["poor_risk_reward"])
        tags = []
        if market_env in {"bull", "strong"}:
            tags.append("market_tailwind")
        sector_strength = _num(features.get("sector_strength", context.get("sector_strength", 0.0)))
        if sector_strength > 0:
            tags.append("sector_confirmed")
        return QualityDecision(True, "", tags)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default
