from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, time
from typing import Any

from .models import PaperPosition, TradingSignal
from .time_utils import cn_market_now, cn_market_time


@dataclass(slots=True)
class RiskResult:
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    require_human_confirmation: bool = False
    approved: bool | None = None
    decision: str = "allow"
    adjusted_order: dict[str, Any] | None = None
    risk_snapshot: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "approved": self.allowed if self.approved is None else self.approved,
            "decision": self.decision,
            "reasons": list(self.reasons),
            "risk_reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "require_human_confirmation": self.require_human_confirmation,
            "required_confirm": self.require_human_confirmation,
            "adjusted_order": self.adjusted_order,
            "risk_snapshot": dict(self.risk_snapshot),
            "mode": "paper_only_no_real_broker",
        }


@dataclass(slots=True)
class RiskGatewayConfig:
    max_total_exposure_pct: float = 0.95
    max_single_position_pct: float = 0.25
    max_industry_exposure_pct: float = 0.35
    max_trade_loss_pct: float = 0.02
    max_daily_loss_pct: float = 0.05
    max_consecutive_losses: int = 3
    max_daily_trade_count: int = 20
    max_turnover_pct: float = 1.5
    min_score: float = 55.0
    min_liquidity_amount: float = 30_000_000.0
    large_order_confirm_amount: float = 100_000.0
    blacklist: set[str] = field(default_factory=set)
    trading_start: time = time(9, 30)
    trading_end: time = time(15, 0)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["blacklist"] = sorted(self.blacklist)
        data["trading_start"] = self.trading_start.isoformat(timespec="minutes")
        data["trading_end"] = self.trading_end.isoformat(timespec="minutes")
        return data


class RiskGateway:
    """Paper-only trading risk gate. It never routes to a real broker."""

    def __init__(
        self,
        *,
        max_single_position_pct: float = 0.25,
        max_total_exposure_pct: float = 0.95,
        min_score: float = 55.0,
        config: RiskGatewayConfig | None = None,
    ) -> None:
        self.config = config or RiskGatewayConfig(
            max_single_position_pct=max_single_position_pct,
            max_total_exposure_pct=max_total_exposure_pct,
            min_score=min_score,
        )
        self.max_single_position_pct = self.config.max_single_position_pct
        self.max_total_exposure_pct = self.config.max_total_exposure_pct
        self.min_score = self.config.min_score

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
        decision = "reject" if reasons else "manual_confirm" if warnings else "allow"
        return RiskResult(
            allowed=not reasons,
            approved=not reasons,
            decision=decision,
            reasons=reasons,
            warnings=warnings,
            require_human_confirmation=bool(warnings),
            adjusted_order=signal.to_dict(),
            risk_snapshot={
                "cash": cash,
                "equity": equity,
                "current_exposure": current_value / max(equity, 1.0),
                "new_exposure": new_value / max(equity, 1.0),
                "paper_only": True,
            },
        )

    def evaluate_order(
        self,
        order: dict[str, Any],
        *,
        portfolio: dict[str, Any] | None = None,
        signal: dict[str, Any] | None = None,
        quote: dict[str, Any] | None = None,
        anomaly: dict[str, Any] | None = None,
        freshness: dict[str, Any] | None = None,
        now: datetime | None = None,
        manual_replay: bool = False,
    ) -> dict[str, Any]:
        cfg = self.config
        portfolio = portfolio or {}
        signal = signal or {}
        quote = quote or {}
        anomaly = anomaly or {}
        freshness = freshness or {}
        order = dict(order or {})
        side = str(order.get("side") or signal.get("action") or "").lower()
        symbol = str(order.get("symbol") or signal.get("symbol") or "").strip()
        quantity = int(order.get("quantity") or 0)
        price = self._num(order.get("price") or quote.get("last") or quote.get("price"))
        order_amount = abs(quantity * price)
        equity = self._num(portfolio.get("equity"), self._num(portfolio.get("cash"), 0.0))
        cash = self._num(portfolio.get("cash"), 0.0)
        current_positions = portfolio.get("positions") or {}
        current_value = sum(self._num(p.get("market_value"), self._num(p.get("quantity"), 0) * self._num(p.get("market_price") or p.get("avg_cost"), 0)) for p in current_positions.values() if isinstance(p, dict))
        current_symbol_value = 0.0
        pos = current_positions.get(symbol) if isinstance(current_positions, dict) else None
        available_quantity = 0
        if isinstance(pos, dict):
            current_symbol_value = self._num(pos.get("market_value"), self._num(pos.get("quantity"), 0) * self._num(pos.get("market_price") or pos.get("avg_cost"), 0))
            available_quantity = int(self._num(pos.get("available_quantity"), self._num(pos.get("quantity"), 0)))
        reasons: list[str] = []
        warnings: list[str] = []
        now = cn_market_time(now) or cn_market_now()

        if side not in {"buy", "sell", "reduce", "add"}:
            reasons.append("订单方向无效")
        if symbol in cfg.blacklist or quote.get("blacklisted"):
            reasons.append("标的在黑名单中")
        if str(quote.get("name") or symbol).startswith(("ST", "*ST")) or quote.get("is_st"):
            reasons.append("ST 或退市风险标的禁止自动通过")
        if not manual_replay and not self._is_trading_time(now):
            reasons.append("非交易时段禁止自动下单")
        if freshness.get("action") == "block" or quote.get("stale"):
            reasons.append("关键行情/分时数据过期")
        elif freshness.get("action") in {"reduce", "refresh_required"}:
            warnings.append("部分数据过期，需刷新或降仓")
        if side in {"buy", "add"} and self._num(signal.get("final_score") or signal.get("score")) < cfg.min_score:
            warnings.append(f"评分低于风控建议线 {cfg.min_score:.1f}")
        if side in {"buy", "add"} and (quote.get("limit_up") or quote.get("is_limit_up")):
            reasons.append("涨停默认不追买")
        if side in {"sell", "reduce"} and (quote.get("limit_down") or quote.get("is_limit_down")):
            reasons.append("跌停默认不卖出")
        if side in {"buy", "add"} and quote.get("amount") is not None and self._num(quote.get("amount")) < cfg.min_liquidity_amount:
            reasons.append("成交额过低，流动性不足")
        if side in {"buy", "add"} and order_amount > cash:
            reasons.append("现金不足")
        if side in {"sell", "reduce"} and quantity > available_quantity:
            reasons.append("可卖数量不足或受 T+1 限制")
        new_total = current_value + (order_amount if side in {"buy", "add"} else 0.0)
        new_symbol = current_symbol_value + (order_amount if side in {"buy", "add"} else -min(order_amount, current_symbol_value))
        if equity > 0 and new_total / equity > cfg.max_total_exposure_pct:
            reasons.append("最大总仓位超限")
        if equity > 0 and new_symbol / equity > cfg.max_single_position_pct:
            reasons.append("最大单票仓位超限")
        industry_exposure = self._num(portfolio.get("industry_exposure"), 0.0)
        if side in {"buy", "add"} and industry_exposure > cfg.max_industry_exposure_pct:
            reasons.append("行业仓位超限")
        if self._num(portfolio.get("daily_pnl_pct"), 0.0) <= -abs(cfg.max_daily_loss_pct):
            reasons.append("当日亏损超过上限")
        if int(portfolio.get("loss_streak") or portfolio.get("consecutive_losses") or 0) >= cfg.max_consecutive_losses:
            reasons.append("连续亏损超过上限")
        if int(portfolio.get("trade_count_today") or 0) >= cfg.max_daily_trade_count:
            reasons.append("日内交易次数超过上限")
        if self._num(portfolio.get("turnover_pct"), 0.0) > cfg.max_turnover_pct:
            reasons.append("换手率超过上限")
        if anomaly.get("action_suggestion") in {"block_buy", "force_exit"} and side in {"buy", "add"}:
            reasons.append("异常波动禁止买入")
        if anomaly.get("action_suggestion") == "manual_confirm":
            warnings.append("异常波动需要人工确认")
        if signal.get("action") == "avoid" or signal.get("info_negative_veto"):
            reasons.append("信息面重大负面 veto")
        if order_amount >= cfg.large_order_confirm_amount:
            warnings.append("单笔金额较大，需要人工确认")
        decision = "reject" if reasons else "manual_confirm" if warnings else "allow"
        approved = not reasons
        return {
            "approved": approved,
            "allowed": approved,
            "decision": decision,
            "adjusted_order": order,
            "risk_reasons": list(dict.fromkeys(reasons)),
            "reasons": list(dict.fromkeys(reasons)),
            "warnings": list(dict.fromkeys(warnings)),
            "required_confirm": bool(warnings),
            "require_human_confirmation": bool(warnings),
            "risk_snapshot": {
                "cash": round(cash, 6),
                "equity": round(equity, 6),
                "order_amount": round(order_amount, 6),
                "current_exposure": round(current_value / max(equity, 1.0), 6),
                "new_exposure": round(new_total / max(equity, 1.0), 6),
                "single_position_pct": round(new_symbol / max(equity, 1.0), 6),
                "available_quantity": available_quantity,
                "paper_only": True,
                "real_broker_connected": False,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "paper_only": True,
            "real_broker_connected": False,
            **self.config.to_dict(),
        }

    def _num(self, value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def _is_trading_time(self, value: datetime) -> bool:
        market_time = cn_market_time(value) or cn_market_now()
        t = market_time.time()
        return time(9, 30) <= t <= time(11, 30) or time(13, 0) <= t <= time(15, 0)
