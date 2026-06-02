from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .score_provenance import ScoreProvenance


@dataclass(slots=True)
class SignalDecision:
    signal_id: str
    symbol: str
    decision_time: str
    strategy_family: str
    action: str
    final_score: float
    confidence: float
    target_weight: float
    reason_summary: str
    score_provenance_id: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SignalFusion:
    """Turn a scored provenance object into a paper/backtest signal decision."""

    def decide(
        self,
        provenance: ScoreProvenance,
        *,
        strategy_family: str | None = None,
        buy_score: float = 62.0,
        sell_score: float = 48.0,
        max_weight: float = 0.25,
    ) -> SignalDecision:
        family = strategy_family or provenance.strategy_family
        score = float(provenance.final_score)
        if not provenance.no_lookahead:
            action = "avoid"
            reason = "评分包含未来可用数据，禁止交易"
        elif score >= buy_score:
            action = "buy"
            reason = f"评分 {score:.1f} 达到买入阈值 {buy_score:.1f}"
        elif score <= sell_score:
            action = "sell"
            reason = f"评分 {score:.1f} 低于卖出阈值 {sell_score:.1f}"
        else:
            action = "hold"
            reason = "评分位于观察区间"
        confidence = min(0.95, max(0.1, provenance.coverage_pct / 100 * (0.55 + abs(score - 50) / 100)))
        target_weight = 0.0 if action != "buy" else min(max_weight, max_weight * score / 100)
        return SignalDecision(
            signal_id=f"sig-{provenance.score_provenance_id[3:]}",
            symbol=provenance.symbol,
            decision_time=provenance.decision_time,
            strategy_family=family,
            action=action,
            final_score=round(score, 4),
            confidence=round(confidence, 4),
            target_weight=round(target_weight, 6),
            reason_summary=reason,
            score_provenance_id=provenance.score_provenance_id,
            warnings=list(provenance.warnings),
        )
