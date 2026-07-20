from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .strategy_family import normalize_strategy_family


@dataclass(slots=True)
class ExitSignal:
    action: str
    policy: str
    reason: str
    confidence: float = 0.5
    partial_ratio: float = 1.0
    risk_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExitPolicyV323:
    def evaluate(self, position: dict[str, Any], market: dict[str, Any], *, strategy_family: str = "swing") -> ExitSignal:
        family = normalize_strategy_family(strategy_family, default="swing")
        pnl = _num(position.get("unrealized_pct"))
        score = _num(market.get("score"), 50.0)
        flags = list(market.get("risk_flags") or [])
        joined_flags = " ".join(str(flag) for flag in flags)
        if "重大负面" in joined_flags:
            return ExitSignal("sell", "major_negative_veto", "重大负面事件触发清仓建议", 0.9, risk_flags=flags)
        if family in {"short", "swing"} and pnl <= -abs(_num(market.get("stop_loss_pct"), 0.08)):
            return ExitSignal("sell", "fixed_stop_loss", "触发止损", 0.82, risk_flags=flags)
        if family == "position" and (score < 42 or "基本面恶化" in joined_flags):
            return ExitSignal("reduce", "thesis_break_exit", "中长线持有逻辑破坏，建议减仓或退出", 0.78, risk_flags=flags)
        if _num(market.get("take_profit_pct")) and pnl >= _num(market.get("take_profit_pct")):
            return ExitSignal("reduce", "staged_take_profit", "达到分批止盈条件", 0.7, partial_ratio=0.5)
        if score < 45:
            return ExitSignal("reduce", "score_decay_exit", "评分衰减至卖出观察区", 0.62)
        return ExitSignal("hold", "no_exit", "未触发退出规则", 0.55)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except Exception:
        return default
