from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .data_loader import date_text, field_value, number
from .market_rules import MarketRuleEngine, RuleProfile
from .models import BacktestConfig, Fill, Order, Position


@dataclass(slots=True)
class ExecutionDecision:
    fill: Fill | None
    status: str
    reason: str


class ExecutionSimulator:
    """A-share execution simulator: T+1, 100-share lots, no shorting and limit checks."""

    def __init__(self, rule_engine: MarketRuleEngine | None = None) -> None:
        self.rule_engine = rule_engine or MarketRuleEngine.default()

    def execute_order(
        self,
        order: Order,
        execution_bar: Any,
        *,
        cash: float,
        position: Position | None = None,
        config: BacktestConfig | None = None,
    ) -> ExecutionDecision:
        cfg = config or BacktestConfig()
        execution_date = date_text(field_value(execution_bar, "ts", field_value(execution_bar, "date", order.date)))
        rule = self.rule_engine.resolve_profile(
            order.symbol,
            asof=execution_date,
            security_master={
                "security_type": field_value(execution_bar, "security_type", ""),
                "exchange": field_value(execution_bar, "exchange", ""),
                "board": field_value(execution_bar, "board", ""),
                "risk_warning_status": field_value(execution_bar, "risk_warning_status", field_value(execution_bar, "is_st", False)),
                "price_limit_profile_id": field_value(execution_bar, "price_limit_profile_id", ""),
            },
        )
        if self._order_type(order, cfg) not in set(rule.order_types_allowed):
            return self._blocked(order, execution_date, f"规则 {rule.profile_id} 不支持订单类型 {self._order_type(order, cfg)}")
        use_t_plus_one = bool(cfg.t_plus_one and rule.t_plus_one)
        if use_t_plus_one and order.signal_date and execution_date <= order.signal_date:
            return self._blocked(order, execution_date, "T+1：成交日必须晚于信号日")
        if field_value(execution_bar, "suspended", False) or number(field_value(execution_bar, "volume")) <= 0:
            return self._blocked(order, execution_date, "停牌或零成交量，无法成交")
        if order.side == "buy" and self._is_limit_up(execution_bar, rule) and not cfg.allow_limit_up_buy:
            return self._blocked(order, execution_date, "涨停无法买入")
        if order.side == "sell" and self._is_limit_down(execution_bar, rule) and not cfg.allow_limit_down_sell:
            return self._blocked(order, execution_date, "跌停无法卖出")
        limit_decision = self._limit_touch_decision(order, execution_bar, execution_date, cfg)
        if limit_decision is not None:
            return limit_decision

        price = self._execution_price(order, execution_bar, cfg)
        if price <= 0:
            return self._blocked(order, execution_date, "价格无效")
        requested = self._requested_quantity(order, price, cash, position, cfg)
        if order.side != "sell":
            requested = self._round_order_quantity(requested, order.side, cfg, rule, sell_all=False)
        if requested <= 0:
            return self._blocked(order, execution_date, "数量不足一手或现金/持仓不足")
        if cfg.min_trade_amount and requested * price < cfg.min_trade_amount:
            return self._blocked(order, execution_date, "低于最小交易金额")
        max_qty = self._volume_cap(execution_bar, cfg)
        if order.side == "sell":
            available = (position.available_quantity if position else 0) if use_t_plus_one else (position.quantity if position else 0)
            sell_all = requested >= available > 0
            quantity = min(requested, max_qty, available)
            quantity = self._round_order_quantity(quantity, order.side, cfg, rule, sell_all=sell_all and quantity >= available)
            if quantity <= 0:
                return self._blocked(order, execution_date, "T+1 可卖数量不足")
        else:
            quantity = min(requested, max_qty)
            quantity = self._round_order_quantity(quantity, order.side, cfg, rule, sell_all=False)
            if quantity <= 0:
                return self._blocked(order, execution_date, "成交量限制后不足一手")
        reference_price = self._base_execution_price(order, execution_bar, cfg)
        commission, stamp_tax, transfer_fee, slippage_cost, cash_cost = self._costs(order.side, quantity, price, cfg, reference_price)
        gross = quantity * price
        if order.side == "buy" and gross + cash_cost > cash + 1e-6:
            affordable = int((cash - cfg.min_commission) / max(price, 1e-9))
            quantity = self._round_lot(min(quantity, affordable), cfg.lot_size)
            if quantity <= 0:
                return self._blocked(order, execution_date, "现金不足")
            commission, stamp_tax, transfer_fee, slippage_cost, cash_cost = self._costs(order.side, quantity, price, cfg, reference_price)
            gross = quantity * price
        fill = Fill(
            fill_id=f"fill-{order.order_id}",
            order_id=order.order_id,
            symbol=order.symbol,
            date=execution_date,
            side=order.side,
            quantity=quantity,
            requested_quantity=requested,
            price=round(price, 6),
            gross_amount=round(gross, 6),
            commission=round(commission, 6),
            stamp_tax=round(stamp_tax, 6),
            transfer_fee=round(transfer_fee, 6),
            slippage_cost=round(slippage_cost, 6),
            cash_cost=round(cash_cost, 6),
            slippage_mode=cfg.slippage_mode,
            reason=order.reason,
            partial=quantity < requested,
        )
        order.status = "filled" if not fill.partial else "partial"
        order.status_reason = "成交"
        return ExecutionDecision(fill=fill, status="filled" if not fill.partial else "partial", reason="成交")

    def _blocked(self, order: Order, date: str, reason: str) -> ExecutionDecision:
        fill = Fill(
            fill_id=f"blocked-{order.order_id}",
            order_id=order.order_id,
            symbol=order.symbol,
            date=date,
            side=order.side,
            quantity=0,
            requested_quantity=max(0, int(order.quantity or 0)),
            price=0.0,
            gross_amount=0.0,
            reason=reason,
            blocked=True,
        )
        order.status = "blocked"
        order.status_reason = reason
        return ExecutionDecision(fill=fill, status="blocked", reason=reason)

    def _execution_price(self, order: Order, bar: Any, cfg: BacktestConfig) -> float:
        base = self._base_execution_price(order, bar, cfg)
        if cfg.slippage_mode == "explicit_slippage_cost":
            return base
        slip = cfg.slippage_bps / 10000
        price = base * (1 + slip if order.side == "buy" else 1 - slip)
        if self._order_type(order, cfg) == "limit" and order.limit_price:
            limit = float(order.limit_price)
            price = min(price, limit) if order.side == "buy" else max(price, limit)
        return price

    def _base_execution_price(self, order: Order, bar: Any, cfg: BacktestConfig) -> float:
        order_type = self._order_type(order, cfg)
        if order_type == "next_close":
            base = number(field_value(bar, "close"))
        elif order_type == "vwap":
            amount = number(field_value(bar, "amount"))
            volume = number(field_value(bar, "volume"))
            base = amount / max(volume * 100, 1.0) if amount > 0 and volume > 0 else number(field_value(bar, "open"))
        elif order_type == "limit" and order.limit_price:
            limit = float(order.limit_price)
            open_price = number(field_value(bar, "open"), limit)
            if cfg.limit_open_better:
                base = min(open_price, limit) if order.side == "buy" else max(open_price, limit)
            else:
                base = limit
        else:
            base = number(field_value(bar, "open"))
        return base

    def _limit_touch_decision(self, order: Order, bar: Any, execution_date: str, cfg: BacktestConfig) -> ExecutionDecision | None:
        if self._order_type(order, cfg) != "limit" or order.limit_price is None:
            return None
        limit = float(order.limit_price)
        high = number(field_value(bar, "high"))
        low = number(field_value(bar, "low"))
        if low <= limit <= high:
            return None
        order.attempts += 1
        valid_days = max(1, int(order.expires_after_days or cfg.order_valid_days or 1))
        reason = f"限价未触达 {limit:.4f}，当日区间 {low:.4f}-{high:.4f}"
        fill = Fill(
            fill_id=f"pending-{order.order_id}-{order.attempts}",
            order_id=order.order_id,
            symbol=order.symbol,
            date=execution_date,
            side=order.side,
            quantity=0,
            requested_quantity=max(0, int(order.quantity or 0)),
            price=0.0,
            gross_amount=0.0,
            reason=reason if order.attempts < valid_days else f"{reason}，订单过期",
            blocked=True,
        )
        if order.attempts < valid_days:
            order.status = "pending"
            order.status_reason = reason
            return ExecutionDecision(fill=fill, status="pending", reason=reason)
        order.status = "expired"
        order.status_reason = fill.reason
        return ExecutionDecision(fill=fill, status="expired", reason=fill.reason)

    def _requested_quantity(self, order: Order, price: float, cash: float, position: Position | None, cfg: BacktestConfig) -> int:
        if order.quantity > 0:
            return int(order.quantity)
        if order.side == "sell":
            return int(position.quantity if position else 0)
        if order.target_weight:
            budget = cash * min(max(float(order.target_weight), 0.0), cfg.max_single_position_pct)
        else:
            budget = cash * min(max(cfg.position_pct, 0.0), 1.0)
        return int(budget / max(price, 1e-9))

    @staticmethod
    def _round_lot(quantity: int | float, lot_size: int) -> int:
        lot = max(1, int(lot_size or 100))
        return max(0, int(quantity) // lot * lot)

    def _round_order_quantity(self, quantity: int | float, side: str, cfg: BacktestConfig, rule: RuleProfile, *, sell_all: bool) -> int:
        if side == "sell" and sell_all and rule.odd_lot_sell_once:
            return max(0, int(quantity))
        return self._round_lot(quantity, int(rule.lot_size_buy or cfg.lot_size or 100))

    @staticmethod
    def _volume_cap(bar: Any, cfg: BacktestConfig) -> int:
        volume = number(field_value(bar, "volume"))
        volume_shares = volume * 100 if volume < 50_000_000 else volume
        return max(0, int(volume_shares * max(0.0, min(cfg.volume_limit_pct, 1.0))))

    def _is_limit_up(self, bar: Any, rule: RuleProfile) -> bool:
        if field_value(bar, "limit_up", False) or field_value(bar, "is_limit_up", False):
            return True
        limit_price = number(field_value(bar, "limit_up_price"))
        close = number(field_value(bar, "close"))
        if limit_price > 0 and close >= limit_price - max(rule.price_tick, 0.001):
            return True
        return number(field_value(bar, "change_pct")) >= rule.price_limit_pct * 100 - 0.5

    def _is_limit_down(self, bar: Any, rule: RuleProfile) -> bool:
        if field_value(bar, "limit_down", False) or field_value(bar, "is_limit_down", False):
            return True
        limit_price = number(field_value(bar, "limit_down_price"))
        close = number(field_value(bar, "close"))
        if limit_price > 0 and close <= limit_price + max(rule.price_tick, 0.001):
            return True
        return number(field_value(bar, "change_pct")) <= -(rule.price_limit_pct * 100 - 0.5)

    @staticmethod
    def _order_type(order: Order, cfg: BacktestConfig) -> str:
        if order.order_type == "next_open" and cfg.order_type != "next_open":
            return cfg.order_type
        return order.order_type

    @staticmethod
    def _limit_threshold(symbol: str, cfg: BacktestConfig | None = None) -> float:
        """Backward-compatible shim; execution uses MarketRuleEngine profiles."""
        cfg = cfg or BacktestConfig()
        rule = MarketRuleEngine.default().resolve_profile(str(symbol or ""))
        return rule.price_limit_pct * 100 if rule.profile_id != "UNSPECIFIED" else cfg.price_limit_main_pct

    @staticmethod
    def _costs(side: str, quantity: int, price: float, cfg: BacktestConfig, reference_price: Any = None) -> tuple[float, float, float, float, float]:
        gross = quantity * price
        commission = max(cfg.min_commission, gross * cfg.commission_rate) if gross > 0 else 0.0
        stamp_tax = gross * cfg.stamp_tax_rate if side == "sell" else 0.0
        transfer_fee = gross * cfg.transfer_fee_rate
        reference = number(reference_price, price)
        if cfg.slippage_mode == "explicit_slippage_cost":
            slippage_cost = abs(reference) * abs(quantity) * max(cfg.slippage_bps, 0.0) / 10000
            cash_cost = commission + stamp_tax + transfer_fee + slippage_cost
        else:
            slippage_cost = abs(price - reference) * quantity
            cash_cost = commission + stamp_tax + transfer_fee
        return commission, stamp_tax, transfer_fee, slippage_cost, cash_cost
