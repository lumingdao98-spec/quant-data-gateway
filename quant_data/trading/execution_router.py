from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .broker import BrokerAdapter, DisabledBrokerAdapter, LiveOrderRequest
from .order_lifecycle import OrderLifecycle
from .order_models import UnifiedOrder


@dataclass(slots=True)
class ExecutionRouteResult:
    ok: bool
    mode: str
    order: dict[str, Any]
    broker_ack: dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExecutionRouter:
    def __init__(self, broker: BrokerAdapter | None = None) -> None:
        self.broker = broker or DisabledBrokerAdapter()
        self.lifecycle = OrderLifecycle()

    def route(self, order: UnifiedOrder, *, confirmed: bool = False) -> ExecutionRouteResult:
        if order.mode == "backtest":
            self.lifecycle.transition(order, "accepted", "回测订单交由历史撮合器处理")
            return ExecutionRouteResult(True, order.mode, order.to_dict(), reason="backtest")
        if order.mode == "realtime_paper":
            self.lifecycle.transition(order, "accepted", "实时模拟订单交由 paper gateway 处理")
            return ExecutionRouteResult(True, order.mode, order.to_dict(), reason="paper")
        if not confirmed:
            self.lifecycle.transition(order, "needs_confirmation", "真实订单必须人工确认")
            return ExecutionRouteResult(False, order.mode, order.to_dict(), reason="needs_confirmation")
        self.lifecycle.transition(order, "submitted", "真实订单提交券商适配器")
        ack = self.broker.place_order(
            LiveOrderRequest(
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                order_type=order.order_type,
                limit_price=order.limit_price,
                target_weight=order.target_weight,
                strategy_family=order.strategy_family,
                signal_id=order.signal_id,
                provenance_id=order.provenance_id,
                risk_check_id=order.risk_check_id,
                source_page=order.source_page,
            )
        )
        self.lifecycle.transition(order, "accepted" if ack.accepted else "rejected", ack.reason or ack.status)
        order.broker_order_id = ack.broker_order_id
        return ExecutionRouteResult(ack.accepted, order.mode, order.to_dict(), ack.to_dict(), ack.reason)
