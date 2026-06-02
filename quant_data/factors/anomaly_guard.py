from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .score_provenance import GateResult


@dataclass(slots=True)
class FactorAnomalyResult:
    blocked: bool
    penalty: float
    warnings: list[str] = field(default_factory=list)
    gates: list[GateResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["gates"] = [x.to_dict() for x in self.gates]
        return data


class FactorAnomalyGuard:
    """Translate abnormal data/events into score gates and penalties."""

    def check(self, features: dict[str, Any] | None = None, events: list[dict[str, Any]] | None = None) -> FactorAnomalyResult:
        features = features or {}
        events = events or []
        warnings: list[str] = []
        gates: list[GateResult] = []
        penalty = 0.0
        blocked = False
        if features.get("suspended"):
            blocked = True
            penalty += 50
            warnings.append("证券停牌")
        if features.get("is_st") or features.get("risk_warning"):
            penalty += 18
            warnings.append("风险警示状态")
        if _num(features.get("source_stale_minutes")) >= 10:
            penalty += 12
            warnings.append("数据源陈旧")
        text = " ".join(str(x.get("title") or x.get("tag") or x) for x in events)
        if any(k in text for k in ["立案", "退市", "暴雷", "处罚"]):
            blocked = True
            penalty += 35
            warnings.append("重大负面事件")
        gates.append(GateResult("anomaly_guard", not blocked, "；".join(warnings), penalty, ["events", "quote"]))
        return FactorAnomalyResult(blocked=blocked, penalty=round(penalty, 4), warnings=list(dict.fromkeys(warnings)), gates=gates)


def _num(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0
