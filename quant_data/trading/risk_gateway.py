from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import PaperPosition, TradingSignal


@dataclass(slots=True)
class RiskResult:
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    require_human_confirmation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "require_human_confirmation": self.require_human_confirmation,
            "mode": "paper_only_no_real_broker",
        }


class RiskGateway:
    """Paper-only trading risk gate. It never routes to a real broker."""

    def __init__(
        self,
        *,
        max_single_position_pct: float = 0.25,
        max_total_exposure_pct: float = 0.95,
        min_score: float = 55.0,
    ) -> None:
        self.max_single_position_pct = max_single_position_pct
        self.max_total_exposure_pct = max_total_exposure_pct
        self.min_score = min_score

    def check(
        self,
        signal: TradingSignal,
        *,
        cash: float,
        equity: float,
        positions: dict[str, PaperPosition],
        quote: dict[str, Any] | None = None,
    ) -> RiskResult:
        quote = quote or {}
        reasons: list[str] = []
        warnings: list[str] = []
        side = signal.side.lower()
        if side not in {"buy", "sell"}:
            reasons.append("side 必须是 buy/sell")
        if signal.symbol.startswith(("ST", "*ST")) or quote.get("is_st"):
            reasons.append("ST 或退市风险标的禁止自动通过")
        if side == "buy" and signal.score < self.min_score:
            warnings.append(f"评分 {signal.score:.1f} 低于风控建议线 {self.min_score:.1f}")
        if side == "buy" and (quote.get("limit_up") or quote.get("is_limit_up")):
            reasons.append("涨停默认不追买")
        if side == "sell" and (quote.get("limit_down") or quote.get("is_limit_down")):
            reasons.append("跌停默认不卖出")
        price = float(signal.price or quote.get("price") or quote.get("last") or 0.0)
        quantity = int(signal.quantity or 0)
        if side == "buy" and quantity > 0 and price > 0 and quantity * price > cash:
            reasons.append("现金不足")
        current_value = sum(p.market_value or p.quantity * (p.market_price or p.avg_cost) for p in positions.values())
        new_value = current_value + (quantity * price if side == "buy" else 0.0)
        if equity > 0 and new_value / equity > self.max_total_exposure_pct:
            reasons.append("总仓位超过风险上限")
        if side == "buy" and equity > 0 and quantity * price / equity > self.max_single_position_pct:
            reasons.append("单票仓位超过风险上限")
        if quote.get("stale"):
            warnings.append("行情数据疑似过期")
        return RiskResult(allowed=not reasons, reasons=reasons, warnings=warnings, require_human_confirmation=bool(warnings))

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "paper_only": True,
            "real_broker_connected": False,
            "max_single_position_pct": self.max_single_position_pct,
            "max_total_exposure_pct": self.max_total_exposure_pct,
            "min_score": self.min_score,
        }
