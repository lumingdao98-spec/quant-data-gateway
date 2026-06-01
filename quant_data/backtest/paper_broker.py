from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from .execution import ExecutionSimulator
from .models import BacktestConfig, Fill, Order, StrategySignal
from .portfolio import PortfolioManager


class PaperBroker:
    """Paper-trading adapter. It never talks to a real broker."""

    def __init__(self, config: BacktestConfig | None = None) -> None:
        self.config = config or BacktestConfig()
        self.portfolio = PortfolioManager(self.config)
        self.execution = ExecutionSimulator()
        self.orders: list[Order] = []
        self.fills: list[Fill] = []
        self.events: list[dict[str, Any]] = []

    def receive_signal(self, signal: StrategySignal) -> Order | None:
        if signal.action not in {"buy", "sell"}:
            self.events.append({"type": "ignored_signal", "signal": signal.to_dict(), "time": self._now()})
            return None
        order = Order(
            order_id=f"paper-{uuid4().hex[:10]}",
            symbol=signal.symbol,
            date=signal.date,
            side=signal.action,
            target_weight=signal.target_weight,
            order_type=self.config.order_type,
            signal_date=signal.date,
            signal_score=signal.score,
            reason=f"纸面交易信号：{signal.reason}",
        )
        self.orders.append(order)
        self.events.append({"type": "order_created", "order": order.to_dict(), "time": self._now()})
        return order

    def simulate_fill(self, order: Order, bar: Any) -> Fill | None:
        decision = self.execution.execute_order(
            order,
            bar,
            cash=self.portfolio.cash,
            position=self.portfolio.positions.get(order.symbol),
            config=self.config,
        )
        if decision.fill:
            self.fills.append(decision.fill)
            self.portfolio.apply_fill(decision.fill)
            self.events.append({"type": decision.status, "reason": decision.reason, "fill": decision.fill.to_dict(), "time": self._now()})
        return decision.fill

    def snapshot(self, date: str | None = None) -> dict[str, Any]:
        state = self.portfolio.mark_to_market({}, date or self._now())
        return {
            "cash": state.cash,
            "equity": state.equity,
            "positions": {k: v.to_dict() for k, v in self.portfolio.positions.items()},
            "orders": [x.to_dict() for x in self.orders],
            "fills": [x.to_dict() for x in self.fills],
            "events": list(self.events),
            "disclaimer": "纸面交易仅用于研究辅助，不构成投资建议；未接入真实券商。",
        }

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")
