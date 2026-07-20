from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from quant_data.data.events_snapshot import EventSnapshot
from quant_data.strategy.strategy_family import normalize_strategy_family


@dataclass(slots=True)
class EventTriggerDecision:
    event_id: str
    decision_time: str
    strategy_family: str
    action: str
    passed: bool
    reason: str
    score_adjustment: float = 0.0
    gates: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EventTriggerEngine:
    def evaluate(self, event: EventSnapshot | dict[str, Any], *, decision_time: str, strategy_family: str = "core_satellite") -> EventTriggerDecision:
        data = event.to_dict() if isinstance(event, EventSnapshot) else dict(event or {})
        family = normalize_strategy_family(strategy_family)
        available_at = str(data.get("available_at") or "")
        if not available_at or available_at > decision_time:
            return EventTriggerDecision(
                str(data.get("event_id") or ""), decision_time, family, "hold", False,
                "事件在决策时点尚不可得，禁止用于评分或交易。",
                gates=[{"gate_key": "pit_available_at", "passed": False, "severity": "block"}],
            )
        if str(data.get("quality_status") or "") != "ok" or data.get("missing_reasons"):
            return EventTriggerDecision(
                str(data.get("event_id") or ""), decision_time, family, "hold", False,
                "事件来源或关键字段不完整，只能展示，不能触发自动交易。",
                gates=[{"gate_key": "event_data_quality", "passed": False, "severity": "block"}],
            )
        direction = str(data.get("impact_direction") or "neutral").lower()
        impact = _num(data.get("impact_score"))
        confidence = max(0.0, min(1.0, _num(data.get("confidence"), 0.5)))
        adjustment = max(-12.0, min(12.0, impact * confidence * 0.12))
        if direction == "negative" and impact <= -60:
            return EventTriggerDecision(
                str(data.get("event_id") or ""), decision_time, family, "risk_block", True,
                "高影响负面事件触发新增仓位阻断，已有仓位进入人工复核。", adjustment,
                gates=[{"gate_key": "major_negative_event", "passed": False, "severity": "block"}],
            )
        if direction == "positive" and family == "event_driven":
            return EventTriggerDecision(
                str(data.get("event_id") or ""), decision_time, family, "review", True,
                "正面事件进入事件驱动候选，但仍需评分、风控和人工确认，不会单独自动买入。", adjustment,
                gates=[{"gate_key": "event_requires_full_precheck", "passed": True, "severity": "info"}],
            )
        return EventTriggerDecision(
            str(data.get("event_id") or ""), decision_time, family, "hold", True,
            "事件已纳入证据链，未单独触发交易动作。", adjustment,
            gates=[{"gate_key": "pit_available_at", "passed": True, "severity": "info"}],
        )


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except Exception:
        return default
