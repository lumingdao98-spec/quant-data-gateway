from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .data_loader import date_text, field_value, number
from .models import BacktestConfig, Fill, Order, Position


@dataclass(slots=True)
class ExecutionDecision:
    fill: Fill | None
    status: str
    reason: str


class ExecutionSimulator:
    """A-share execution simulator: T+1, 100-share lots, no shorting and limit checks."""

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
        if cfg.t_plus_one and order.signal_date and execution_date <= order.signal_date:
            return self._blocked(order, execution_date, "T+1：成交日必须晚于信号日")
        if field_value(execution_bar, "suspended", False) or number(field_value(execution_bar, "volume")) <= 0:
            return self._blocked(order, execution_date, "停牌或零成交量，无法成交")
        if order.side == "buy" and self._is_limit_up(execution_bar):
            return self._blocked(order, execution_date, "涨停无法买入")
        if order.side == "sell" and self._is_limit_down(execution_bar):
            return self._blocked(order, execution_date, "跌停无法卖出")

        price = self._execution_price(order, execution_bar, cfg)
        if price <= 0:
            return self._blocked(order, execution_date, "价格无效")
        requested = self._requested_quantity(order, price, cash, position, cfg)
        requested = self._round_lot(requested, cfg.lot_size)
        if requested <= 0:
            return self._blocked(order, execution_date, "数量不足一手或现金/持仓不足")
        max_qty = self._volume_cap(execution_bar, cfg)
        quantity = min(requested, max_qty)
        quantity = self._round_lot(quantity, cfg.lot_size)
        if quantity <= 0:
            return self._blocked(order, execution_date, "成交量限制后不足一手")
        if order.side == "sell":
            available = (position.available_quantity if position else 0) if cfg.t_plus_one else (position.quantity if position else 0)
            quantity = self._round_lot(min(quantity, available), cfg.lot_size)
            if quantity <= 0:
                return self._blocked(order, execution_date, "T+1 可卖数量不足")
        commission, stamp_tax, transfer_fee, slippage_cost = self._costs(order.side, quantity, price, cfg, field_value(execution_bar, "open"))
        gross = quantity * price
        if order.side == "buy" and gross + commission + transfer_fee + slippage_cost > cash + 1e-6:
            affordable = int((cash - cfg.min_commission) / max(price * (1 + cfg.slippage_bps / 10000), 1e-9))
            quantity = self._round_lot(min(quantity, affordable), cfg.lot_size)
            if quantity <= 0:
                return self._blocked(order, execution_date, "现金不足")
            commission, stamp_tax, transfer_fee, slippage_cost = self._costs(order.side, quantity, price, cfg, field_value(execution_bar, "open"))
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
            reason=order.reason,
            partial=quantity < requested,
        )
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
        return ExecutionDecision(fill=fill, status="blocked", reason=reason)

    def _execution_price(self, order: Order, bar: Any, cfg: BacktestConfig) -> float:
        if order.order_type == "next_close":
            base = number(field_value(bar, "close"))
        elif order.order_type == "vwap":
            amount = number(field_value(bar, "amount"))
            volume = number(field_value(bar, "volume"))
            base = amount / max(volume * 100, 1.0) if amount > 0 and volume > 0 else number(field_value(bar, "open"))
        elif order.order_type == "limit" and order.limit_price:
            base = float(order.limit_price)
        else:
            base = number(field_value(bar, "open"))
        slip = cfg.slippage_bps / 10000
        return base * (1 + slip if order.side == "buy" else 1 - slip)

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

    @staticmethod
    def _volume_cap(bar: Any, cfg: BacktestConfig) -> int:
        volume = number(field_value(bar, "volume"))
        volume_shares = volume * 100 if volume < 50_000_000 else volume
        return max(0, int(volume_shares * max(0.0, min(cfg.volume_limit_pct, 1.0))))

    @staticmethod
    def _is_limit_up(bar: Any) -> bool:
        if field_value(bar, "limit_up", False) or field_value(bar, "is_limit_up", False):
            return True
        return number(field_value(bar, "change_pct")) >= 9.7

    @staticmethod
    def _is_limit_down(bar: Any) -> bool:
        if field_value(bar, "limit_down", False) or field_value(bar, "is_limit_down", False):
            return True
        return number(field_value(bar, "change_pct")) <= -9.7

    @staticmethod
    def _costs(side: str, quantity: int, price: float, cfg: BacktestConfig, raw_open: Any = None) -> tuple[float, float, float, float]:
        gross = quantity * price
        commission = max(cfg.min_commission, gross * cfg.commission_rate) if gross > 0 else 0.0
        stamp_tax = gross * cfg.stamp_tax_rate if side == "sell" else 0.0
        transfer_fee = gross * cfg.transfer_fee_rate
        reference = number(raw_open, price)
        slippage_cost = abs(price - reference) * quantity
        return commission, stamp_tax, transfer_fee, slippage_cost
