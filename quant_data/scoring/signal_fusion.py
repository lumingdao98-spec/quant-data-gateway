from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from .score_models import ScoreProvenanceV323
from .score_policy import ScorePolicyV323


@dataclass(slots=True)
class TradeSignalV323:
    signal_id: str
    symbol: str
    mode: str
    action: str
    final_score: float
    target_weight: float
    reason: str
    provenance_id: str
    created_at: str
    risk_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SignalFusionV323:
    def __init__(self, policy: ScorePolicyV323 | None = None) -> None:
        self.policy = policy or ScorePolicyV323()

    def fuse(self, provenance: ScoreProvenanceV323) -> TradeSignalV323:
        score = float(provenance.final_score)
        blocked = any((not gate.passed and gate.severity == "block") for gate in provenance.gates)
        if blocked:
            action = "hold"
            reason = "风控门禁未通过，禁止自动交易"
        elif score >= self.policy.buy_threshold:
            action = "buy"
            reason = f"评分 {score:.1f} 达到买入阈值 {self.policy.buy_threshold:.1f}"
        elif score <= self.policy.sell_threshold:
            action = "sell"
            reason = f"评分 {score:.1f} 低于卖出阈值 {self.policy.sell_threshold:.1f}"
        else:
            action = "hold"
            reason = "评分处于观察区间"
        if provenance.mode == "live" and self.policy.live_requires_confirmation and action in {"buy", "sell"}:
            reason += "；真实交易需人工确认"
        target = 0.0 if action == "sell" else min(0.25, max(0.0, (score - 50.0) / 100.0))
        return TradeSignalV323(
            signal_id=f"sig-{provenance.provenance_id[-16:]}",
            symbol=provenance.symbol,
            mode=provenance.mode,
            action=action,
            final_score=round(score, 4),
            target_weight=round(target, 6),
            reason=reason,
            provenance_id=provenance.provenance_id,
            created_at=datetime.now().isoformat(timespec="seconds"),
            risk_flags=[g.reason for g in provenance.gates if not g.passed],
        )
