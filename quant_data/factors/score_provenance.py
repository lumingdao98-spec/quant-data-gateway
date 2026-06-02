from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from hashlib import sha256
from typing import Any


@dataclass(slots=True)
class FactorValue:
    factor_id: str
    symbol: str
    asof_time: str
    factor_key: str
    raw_value: float
    normalized_value: float
    weight: float = 1.0
    source_refs: list[str] = field(default_factory=list)
    available_at: str = ""
    group: str = "technical"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class GateResult:
    gate: str
    passed: bool
    reason: str = ""
    penalty: float = 0.0
    source_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ScoringPolicy:
    policy_id: str = "v3.22-default"
    base_score: float = 50.0
    normalization: str = "0-100-centered"
    weights: dict[str, float] = field(default_factory=dict)
    risk_penalty_scale: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def policy_hash(self) -> str:
        payload = repr(sorted(self.to_dict().items())).encode("utf-8")
        return sha256(payload).hexdigest()[:16]


@dataclass(slots=True)
class ScoreContribution:
    factor_key: str
    group: str
    raw_value: float
    normalized_value: float
    weight: float
    contribution: float
    source_refs: list[str] = field(default_factory=list)
    available_at: str = ""
    used: bool = True
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ScoreProvenance:
    score_provenance_id: str
    symbol: str
    decision_time: str
    asof_time: str
    strategy_family: str
    final_score: float
    base_score: float
    contributions: list[ScoreContribution]
    gates: list[GateResult]
    policy_version_hash: str
    source_refs: list[str] = field(default_factory=list)
    no_lookahead: bool = True
    coverage_pct: float = 100.0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["contributions"] = [x.to_dict() for x in self.contributions]
        data["gates"] = [x.to_dict() for x in self.gates]
        return data


def build_score_provenance(
    symbol: str,
    decision_time: datetime | str,
    asof_time: datetime | str,
    strategy_family: str,
    factor_values: list[FactorValue],
    gate_results: list[GateResult],
    scoring_policy: ScoringPolicy,
) -> ScoreProvenance:
    decision = _iso(decision_time)
    asof = _iso(asof_time)
    score = float(scoring_policy.base_score)
    contributions: list[ScoreContribution] = []
    warnings: list[str] = []
    source_refs: list[str] = []
    used_count = 0
    for factor in factor_values:
        available = factor.available_at or factor.asof_time
        used = bool(not available or available <= asof)
        if not used:
            warnings.append(f"{factor.factor_key} available_at 晚于 asof_time，已排除")
        weight = scoring_policy.weights.get(factor.factor_key, factor.weight)
        contribution = ((float(factor.normalized_value) - 50.0) / 50.0) * float(weight) if used else 0.0
        score += contribution
        used_count += 1 if used else 0
        source_refs.extend(factor.source_refs)
        contributions.append(
            ScoreContribution(
                factor_key=factor.factor_key,
                group=factor.group,
                raw_value=round(float(factor.raw_value), 6),
                normalized_value=round(float(factor.normalized_value), 6),
                weight=round(float(weight), 6),
                contribution=round(contribution, 6),
                source_refs=list(factor.source_refs),
                available_at=available,
                used=used,
                reason="PIT可用" if used else "未来可用数据已剔除",
            )
        )
    for gate in gate_results:
        source_refs.extend(gate.source_refs)
        if not gate.passed:
            score -= abs(float(gate.penalty or 0.0)) * scoring_policy.risk_penalty_scale
            warnings.append(gate.reason or f"{gate.gate} 未通过")
    final_score = max(0.0, min(100.0, score))
    payload = f"{symbol}|{decision}|{asof}|{strategy_family}|{scoring_policy.policy_hash}|{len(contributions)}"
    coverage = 100.0 if not factor_values else used_count / len(factor_values) * 100
    return ScoreProvenance(
        score_provenance_id="sp-" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        symbol=symbol,
        decision_time=decision,
        asof_time=asof,
        strategy_family=strategy_family,
        final_score=round(final_score, 4),
        base_score=round(scoring_policy.base_score, 4),
        contributions=contributions,
        gates=gate_results,
        policy_version_hash=scoring_policy.policy_hash,
        source_refs=sorted(set(source_refs)),
        no_lookahead=all(x.used for x in contributions),
        coverage_pct=round(coverage, 4),
        warnings=list(dict.fromkeys(warnings)),
    )


def _iso(value: datetime | str) -> str:
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    return str(value or "")
