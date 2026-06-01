from __future__ import annotations

from typing import Any

from .data_loader import date_text, field_value, number
from .models import BacktestConfig, Fill, Order, PortfolioState, Position, StrategySignal


class PortfolioManager:
    def __init__(self, config: BacktestConfig | None = None) -> None:
        self.config = config or BacktestConfig()
        self.cash = float(self.config.initial_cash)
        self.positions: dict[str, Position] = {}
        self.realized_pnl = 0.0
        self.last_equity = float(self.config.initial_cash)

    def apply_fill(self, fill: Fill) -> None:
        if fill.blocked or fill.quantity <= 0:
            return
        pos = self.positions.get(fill.symbol, Position(symbol=fill.symbol))
        cost = fill.commission + fill.stamp_tax + fill.transfer_fee + fill.slippage_cost
        if fill.side == "buy":
            total_cost = pos.avg_cost * pos.quantity + fill.gross_amount + cost
            pos.quantity += fill.quantity
            pos.available_quantity += 0 if self.config.t_plus_one else fill.quantity
            pos.avg_cost = total_cost / max(pos.quantity, 1)
            pos.last_price = fill.price
            pos.market_value = pos.quantity * fill.price
            pos.entry_date = pos.entry_date or fill.date
            pos.highest_price = max(pos.highest_price, fill.price)
            self.cash -= fill.gross_amount + cost
        else:
            sell_qty = min(fill.quantity, pos.quantity)
            proceeds = sell_qty * fill.price
            pnl = (fill.price - pos.avg_cost) * sell_qty - cost
            pos.quantity -= sell_qty
            pos.available_quantity = max(0, pos.available_quantity - sell_qty)
            pos.realized_pnl += pnl
            self.realized_pnl += pnl
            pos.last_price = fill.price
            pos.market_value = pos.quantity * fill.price
            self.cash += proceeds - cost
        if pos.quantity <= 0:
            self.positions.pop(fill.symbol, None)
        else:
            self.positions[fill.symbol] = pos

    def unlock_t_plus_one(self) -> None:
        for pos in self.positions.values():
            pos.available_quantity = pos.quantity

    def mark_to_market(self, bars_by_symbol: dict[str, Any], date: str, fills: list[Fill] | None = None) -> PortfolioState:
        fills = fills or []
        market_value = 0.0
        for symbol, pos in list(self.positions.items()):
            bar = bars_by_symbol.get(symbol)
            close = number(field_value(bar, "close"), pos.last_price) if bar is not None else pos.last_price
            pos.last_price = close
            pos.highest_price = max(pos.highest_price, close)
            pos.market_value = pos.quantity * close
            pos.unrealized_pnl = (close - pos.avg_cost) * pos.quantity
            market_value += pos.market_value
            self.positions[symbol] = pos
        equity = self.cash + market_value
        turnover = sum(abs(f.gross_amount) for f in fills if not f.blocked) / max(equity, 1.0)
        cost = sum(f.total_cost for f in fills if not f.blocked)
        daily_return = equity / self.last_equity - 1 if self.last_equity else 0.0
        self.last_equity = equity
        exposure = market_value / max(equity, 1.0)
        return PortfolioState(
            date=date,
            cash=round(self.cash, 6),
            market_value=round(market_value, 6),
            equity=round(equity, 6),
            positions=dict(self.positions),
            daily_return=round(daily_return, 8),
            turnover=round(turnover, 8),
            leverage=round(exposure, 8),
            exposure=round(exposure, 8),
            cost=round(cost, 6),
        )

    def allocate_weights(self, signals: list[StrategySignal]) -> dict[str, float]:
        buys = [s for s in signals if s.action == "buy"]
        buys = sorted(buys, key=lambda x: x.score, reverse=True)[: self.config.max_positions]
        score_sum = sum(max(1.0, s.score) for s in buys) or 1.0
        total_budget = max(0.0, min(1.0 - self.config.cash_reserve_pct, self.config.position_pct))
        return {
            s.symbol: round(min(self.config.max_single_position_pct, total_budget * max(1.0, s.score) / score_sum), 6)
            for s in buys
        }

    def build_orders(self, signals: list[StrategySignal], date: str) -> list[Order]:
        weights = self.allocate_weights(signals)
        orders: list[Order] = []
        for idx, signal in enumerate(signals):
            side = signal.action
            if side not in {"buy", "sell"}:
                continue
            if side == "buy" and signal.symbol not in weights:
                continue
            orders.append(
                Order(
                    order_id=f"{date}-{idx}-{signal.symbol}-{side}",
                    symbol=signal.symbol,
                    date=date,
                    side=side,
                    target_weight=weights.get(signal.symbol, 0.0) if side == "buy" else 0.0,
                    order_type=self.config.order_type,
                    signal_date=signal.date,
                    signal_score=signal.score,
                    reason=signal.reason,
                )
            )
        return orders

    def stop_orders(self, date: str, bars_by_symbol: dict[str, Any]) -> list[Order]:
        orders: list[Order] = []
        for symbol, pos in self.positions.items():
            bar = bars_by_symbol.get(symbol)
            close = number(field_value(bar, "close"), pos.last_price) if bar is not None else pos.last_price
            drawdown = (close / pos.avg_cost - 1) * 100 if pos.avg_cost else 0.0
            from_high = (close / pos.highest_price - 1) * 100 if pos.highest_price else 0.0
            reason = ""
            if self.config.stop_loss_pct and drawdown <= -abs(self.config.stop_loss_pct):
                reason = f"止损触发 {drawdown:.2f}%"
            elif self.config.take_profit_pct and drawdown >= abs(self.config.take_profit_pct):
                reason = f"止盈触发 {drawdown:.2f}%"
            elif self.config.trailing_stop_pct and from_high <= -abs(self.config.trailing_stop_pct):
                reason = f"跟踪止损触发 {from_high:.2f}%"
            if reason:
                orders.append(
                    Order(
                        order_id=f"{date}-stop-{symbol}",
                        symbol=symbol,
                        date=date,
                        side="sell",
                        quantity=pos.available_quantity,
                        order_type=self.config.order_type,
                        signal_date=date,
                        reason=reason,
                    )
                )
        return orders
