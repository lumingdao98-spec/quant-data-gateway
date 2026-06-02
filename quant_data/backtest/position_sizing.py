from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


SizingMode = Literal[
    "fixed_percent",
    "fixed_fractional",
    "equal_weight",
    "score_weighted",
    "volatility_target",
    "atr_risk",
    "fixed_risk_per_trade",
    "fractional_kelly",
    "kelly_capped",
    "equal_risk_contribution",
    "pyramid",
    "dca",
    "core_satellite",
]


@dataclass(slots=True)
class PositionSizingConfig:
    sizing_mode: SizingMode = "score_weighted"
    max_total_exposure: float = 0.95
    max_single_position_pct: float = 0.25
    max_industry_exposure: float = 0.35
    cash_reserve_pct: float = 0.02
    risk_per_trade_pct: float = 0.02
    max_daily_new_positions: int = 3
    max_weekly_turnover: float = 1.5
    min_trade_amount: float = 1000.0
    lot_size: int = 100
    rebalance_tolerance: float = 0.02
    compound_returns: bool = True
    use_realized_pnl_reinvestment: bool = True
    reduce_after_loss_streak: int = 2
    increase_after_win_streak: int = 3
    volatility_lookback: int = 20
    atr_period: int = 14
    kelly_fraction: float = 0.25
    pyramid_step_pct: float = 0.05
    pyramid_max_adds: int = 3
    dca_amount: float = 1000.0
    dca_frequency: str = "monthly"
    target_volatility_pct: float = 0.18
    atr_multiplier: float = 2.0
    initial_cash: float = 100_000.0
    core_weight_pct: float = 0.55
    satellite_weight_pct: float = 0.20

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PositionSizingRequest:
    symbol: str
    price: float
    equity: float
    cash: float
    current_position_value: float = 0.0
    current_weight: float = 0.0
    score: float = 50.0
    target_positions: int = 1
    total_exposure: float = 0.0
    industry_exposure: float = 0.0
    volatility_pct: float | None = None
    atr: float | None = None
    stop_distance_pct: float | None = None
    win_rate: float | None = None
    payoff_ratio: float | None = None
    unrealized_pct: float = 0.0
    pyramid_adds: int = 0
    loss_streak: int = 0
    win_streak: int = 0
    valuation_level: str = "normal"
    market_score: float = 50.0
    signal_target_weight: float | None = None
    reason: str = ""


@dataclass(slots=True)
class PositionSizingDecision:
    symbol: str
    sizing_mode: str
    target_weight: float
    target_value: float
    order_value: float
    quantity: int
    risk_per_trade_pct: float
    blocked: bool = False
    reasons: list[str] = field(default_factory=list)
    attribution: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["actual_weight"] = self.attribution.get("actual_weight", self.target_weight)
        data["risk_budget_used"] = self.attribution.get("risk_budget_used", self.risk_per_trade_pct)
        data["position_utilization"] = self.attribution.get("position_utilization", 0.0)
        data["cash_drag"] = self.attribution.get("cash_drag", 0.0)
        return data


class PositionSizer:
    def __init__(self, config: PositionSizingConfig | None = None) -> None:
        self.config = config or PositionSizingConfig()

    def size(self, req: PositionSizingRequest) -> PositionSizingDecision:
        cfg = self.config
        price = max(float(req.price or 0.0), 0.0)
        equity = max(float(req.equity or 0.0), 0.0)
        if not cfg.compound_returns:
            equity = min(equity or cfg.initial_cash, cfg.initial_cash)
        risk_pct, risk_notes = self._risk_pct(req)
        target_weight, notes, attrs = self._raw_weight(req, risk_pct)
        cap_notes: list[str] = []
        target_weight = self._cap_weight(target_weight, req, cap_notes)
        target_value = max(0.0, target_weight * equity)
        order_value = target_value - max(0.0, float(req.current_position_value or 0.0))
        if abs(order_value) < cfg.min_trade_amount:
            notes.append("低于最小交易额或再平衡容忍区间")
            order_value = 0.0
        quantity = self._round_lot(order_value / price) if price > 0 and order_value > 0 else 0
        blocked = price <= 0 or (target_weight <= 0 and cfg.sizing_mode not in {"pyramid", "dca"})
        if price <= 0:
            notes.append("缺少有效价格")
        attrs.update(
            {
                "equity_base": round(equity, 6),
                "raw_mode": cfg.sizing_mode,
                "current_weight": round(req.current_weight, 6),
                "loss_streak": req.loss_streak,
                "win_streak": req.win_streak,
                "total_exposure": req.total_exposure,
                "industry_exposure": req.industry_exposure,
                "actual_weight": round(target_value / max(equity, 1.0), 6),
                "risk_budget_used": round(min(target_weight, risk_pct), 6),
                "position_utilization": round(min(1.0, (req.total_exposure - req.current_weight + target_weight) / max(cfg.max_total_exposure, 1e-9)), 6),
                "cash_drag": round(max(0.0, req.cash - max(0.0, order_value)) / max(equity, 1.0), 6),
            }
        )
        return PositionSizingDecision(
            symbol=req.symbol,
            sizing_mode=cfg.sizing_mode,
            target_weight=round(target_weight, 6),
            target_value=round(target_value, 6),
            order_value=round(order_value, 6),
            quantity=quantity,
            risk_per_trade_pct=round(risk_pct, 6),
            blocked=blocked,
            reasons=list(dict.fromkeys(risk_notes + notes + cap_notes)),
            attribution=attrs,
        )

    def _raw_weight(self, req: PositionSizingRequest, risk_pct: float) -> tuple[float, list[str], dict[str, Any]]:
        cfg = self.config
        mode = cfg.sizing_mode
        if mode == "fixed_fractional":
            mode = "fixed_percent"
        elif mode == "kelly_capped":
            mode = "fractional_kelly"
        elif mode == "equal_risk_contribution":
            mode = "atr_risk"
        notes: list[str] = []
        attrs: dict[str, Any] = {}
        base = req.signal_target_weight if req.signal_target_weight is not None else cfg.max_single_position_pct
        if mode == "fixed_percent":
            weight = min(float(base), cfg.max_single_position_pct)
            notes.append("固定仓位按总权益比例计算")
        elif mode == "equal_weight":
            weight = min(1.0 / max(1, int(req.target_positions or 1)), cfg.max_single_position_pct)
            notes.append("等权按目标持仓数均分")
        elif mode == "score_weighted":
            score_scale = max(0.0, min(1.0, float(req.score or 0.0) / 100.0))
            market_scale = 0.65 if req.market_score < 40 else 1.0
            weight = cfg.max_single_position_pct * score_scale * market_scale
            attrs["score_scale"] = round(score_scale, 4)
            attrs["market_scale"] = market_scale
            notes.append("评分越高目标仓位越高，大盘弱势降权")
        elif mode == "volatility_target":
            vol = max(float(req.volatility_pct or cfg.target_volatility_pct), 0.0001)
            target_vol = max(float(cfg.target_volatility_pct), 0.0001)
            weight = cfg.max_single_position_pct * min(1.0, target_vol / vol)
            attrs["volatility_pct"] = vol
            notes.append("波动率越高仓位越低")
        elif mode in {"atr_risk", "fixed_risk_per_trade"}:
            stop_distance = self._stop_distance(req)
            if stop_distance <= 0:
                weight = 0.0
                notes.append("缺少 ATR/止损距离，风险仓位无法计算")
            else:
                weight = min(cfg.max_single_position_pct, risk_pct / stop_distance)
                attrs["stop_distance_pct"] = round(stop_distance, 6)
                notes.append("按单笔最大亏损预算反推仓位")
        elif mode == "fractional_kelly":
            wr = min(0.99, max(0.01, float(req.win_rate if req.win_rate is not None else 0.5)))
            payoff = max(0.01, float(req.payoff_ratio if req.payoff_ratio is not None else 1.0))
            full_kelly = wr - (1.0 - wr) / payoff
            weight = max(0.0, full_kelly) * cfg.kelly_fraction
            weight = min(weight, cfg.max_single_position_pct)
            attrs.update({"win_rate": wr, "payoff_ratio": payoff, "full_kelly": round(full_kelly, 6)})
            notes.append("分数凯利已按上限截断")
        elif mode == "pyramid":
            if req.unrealized_pct < cfg.pyramid_step_pct:
                weight = req.current_weight
                notes.append("未达到盈利加仓阶梯，不加仓")
            elif req.pyramid_adds >= cfg.pyramid_max_adds:
                weight = req.current_weight
                notes.append("金字塔加仓次数已达上限")
            else:
                add = min(cfg.satellite_weight_pct / max(1, cfg.pyramid_max_adds), cfg.max_single_position_pct * 0.2)
                weight = min(cfg.max_single_position_pct, req.current_weight + add)
                notes.append("盈利且趋势确认，小比例金字塔加仓")
        elif mode == "dca":
            amount = cfg.dca_amount
            if req.valuation_level == "low":
                amount *= 2.0
            elif req.valuation_level == "high":
                amount *= 0.5
            weight = amount / max(req.equity, 1.0)
            notes.append(f"定投按 {cfg.dca_frequency} 固定金额执行")
        elif mode == "core_satellite":
            score_scale = max(0.0, min(1.0, float(req.score or 0.0) / 100.0))
            weight = cfg.core_weight_pct + cfg.satellite_weight_pct * score_scale
            notes.append("核心仓低频持有，卫星仓按评分调节")
        else:
            weight = min(float(base), cfg.max_single_position_pct)
            notes.append("未知模式回退固定仓位")
        return max(0.0, weight), notes, attrs

    def _cap_weight(self, weight: float, req: PositionSizingRequest, notes: list[str]) -> float:
        cfg = self.config
        before = weight
        weight = min(weight, cfg.max_single_position_pct)
        remaining_total = max(0.0, cfg.max_total_exposure - max(0.0, req.total_exposure - req.current_weight))
        weight = min(weight, remaining_total)
        remaining_industry = max(0.0, cfg.max_industry_exposure - max(0.0, req.industry_exposure - req.current_weight))
        weight = min(weight, remaining_industry)
        if cfg.sizing_mode != "dca":
            weight = max(0.0, weight - max(0.0, cfg.cash_reserve_pct if req.total_exposure <= 0 else 0.0))
        if weight < before:
            notes.append("已按单票/总仓位/行业仓位/现金预留上限截断")
        if cfg.sizing_mode != "dca" and abs(weight - req.current_weight) < cfg.rebalance_tolerance:
            notes.append("目标仓位变化低于再平衡容忍区间")
            return req.current_weight
        return weight

    def _risk_pct(self, req: PositionSizingRequest) -> tuple[float, list[str]]:
        cfg = self.config
        pct = float(cfg.risk_per_trade_pct)
        notes: list[str] = []
        if req.loss_streak >= cfg.reduce_after_loss_streak > 0:
            pct *= 0.5
            notes.append("连续亏损触发降仓保护")
        if req.win_streak >= cfg.increase_after_win_streak > 0:
            pct *= 1.15
            notes.append("连续盈利小幅恢复风险预算")
        return max(0.0, min(pct, cfg.risk_per_trade_pct * 1.25)), notes

    def _stop_distance(self, req: PositionSizingRequest) -> float:
        cfg = self.config
        if req.stop_distance_pct and req.stop_distance_pct > 0:
            return float(req.stop_distance_pct)
        if req.atr and req.price:
            return max(0.0, float(req.atr) * cfg.atr_multiplier / max(float(req.price), 0.0001))
        return 0.0

    def _round_lot(self, shares: float) -> int:
        lot = max(1, int(self.config.lot_size or 1))
        if shares <= 0:
            return 0
        return int(shares // lot) * lot


def size_position(
    signal: Any,
    portfolio: Any,
    risk_budget: Any,
    security_master: Any,
    latest_bar: Any,
    sizing_policy: PositionSizingConfig | dict[str, Any] | None,
) -> PositionSizingDecision:
    """V3.22 functional adapter matching the design-document signature."""

    cfg = sizing_policy if isinstance(sizing_policy, PositionSizingConfig) else PositionSizingConfig(**(sizing_policy or {}))
    symbol = str(_get(signal, "symbol") or _get(security_master, "symbol") or "")
    price = float(_get(latest_bar, "close") or _get(latest_bar, "price") or _get(signal, "price") or 0.0)
    equity = float(_get(portfolio, "equity") or _get(portfolio, "cash") or cfg.initial_cash)
    cash = float(_get(portfolio, "cash") or 0.0)
    current_value = float(_get(portfolio, "current_position_value") or _get(portfolio, "market_value") or 0.0)
    current_weight = current_value / max(equity, 1.0)
    req = PositionSizingRequest(
        symbol=symbol,
        price=price,
        equity=equity,
        cash=cash,
        current_position_value=current_value,
        current_weight=current_weight,
        score=float(_get(signal, "final_score") or _get(signal, "score") or 50.0),
        target_positions=int(_get(portfolio, "target_positions") or 1),
        total_exposure=float(_get(portfolio, "exposure") or current_weight),
        volatility_pct=_get(latest_bar, "volatility_pct"),
        atr=_get(latest_bar, "atr"),
        stop_distance_pct=_get(risk_budget, "stop_distance_pct"),
        signal_target_weight=_get(signal, "target_weight"),
        reason=str(_get(signal, "reason_summary") or _get(signal, "reason") or ""),
    )
    return PositionSizer(cfg).size(req)


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)
