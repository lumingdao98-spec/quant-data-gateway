from __future__ import annotations

from typing import Any

from quant_data.trading.broker import BrokerAdapter, DisabledBrokerAdapter
from quant_data.trading.execution_router import ExecutionRouter
from quant_data.trading.order_models import UnifiedOrder


class LiveOrderService:
    def __init__(self, broker: BrokerAdapter | None = None) -> None:
        self.router = ExecutionRouter(broker or DisabledBrokerAdapter())

    def preview(self, order: UnifiedOrder) -> dict[str, Any]:
        return {"ok": True, "order": order.to_dict(), "requires_confirmation": True, "paper_only_until_confirmed": True}

    def place(self, order: UnifiedOrder, *, confirmed: bool = False) -> dict[str, Any]:
        return self.router.route(order, confirmed=confirmed).to_dict()
