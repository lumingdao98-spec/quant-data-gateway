from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


TradeMode = Literal["backtest", "realtime_paper", "live"]


@dataclass(slots=True)
class FactorContribution:
    factor_key: str
    raw_value: Any
    normalized_value: float
    weight: float
    contribution: float
    source: str = ""
    source_time: str = ""
    available_at: str = ""
    confidence: float = 1.0
    explanation: str = ""
    dimension: str = "technical"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ScoreGate:
    gate_key: str
    passed: bool
    reason: str = ""
    severity: str = "info"
    penalty: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ScoreRequest:
    symbol: str
    decision_time: str
    mode: TradeMode = "backtest"
    strategy_family: str = "hybrid"
    factor_values: dict[str, Any] = field(default_factory=dict)
    data_sources: list[dict[str, Any]] = field(default_factory=list)
    gates: list[ScoreGate] = field(default_factory=list)
    action_hint: str = "hold"


@dataclass(slots=True)
class ScoreProvenanceV323:
    provenance_id: str
    symbol: str
    decision_time: str
    mode: TradeMode
    strategy_family: str
    final_score: float
    action: str
    factor_contributions: list[FactorContribution]
    gates: list[ScoreGate]
    data_sources: list[dict[str, Any]]
    pit_status: str = "unknown"
    missing_data: list[str] = field(default_factory=list)
    stale_data: list[str] = field(default_factory=list)
    policy_version: str = "v3.23-default"
    policy_hash: str = ""
    dimension_scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance_id": self.provenance_id,
            "symbol": self.symbol,
            "decision_time": self.decision_time,
            "mode": self.mode,
            "strategy_family": self.strategy_family,
            "final_score": self.final_score,
            "action": self.action,
            "factor_contributions": [x.to_dict() for x in self.factor_contributions],
            "gates": [x.to_dict() for x in self.gates],
            "data_sources": list(self.data_sources),
            "pit_status": self.pit_status,
            "missing_data": list(self.missing_data),
            "stale_data": list(self.stale_data),
            "policy_version": self.policy_version,
            "policy_hash": self.policy_hash,
            "dimension_scores": dict(self.dimension_scores),
        }
