from __future__ import annotations

from .disabled import DisabledBrokerAdapter
from .broker_models import (
    BrokerAccountSnapshot,
    BrokerCash,
    BrokerConnectionStatus,
    BrokerOrder,
    BrokerPosition,
    CancelOrderResult,
    LiveOrderAck,
    LiveOrderRequest,
)


class SimulatorBrokerAdapter(DisabledBrokerAdapter):
    """Local simulator adapter. It is still not a real broker."""

    def __init__(self, initial_cash: float = 100_000.0) -> None:
        super().__init__()
        self.cash = float(initial_cash)
        self.orders: dict[str, BrokerOrder] = {}

    def health_check(self) -> BrokerConnectionStatus:
        return BrokerConnectionStatus(connected=True, status="simulator", broker="simulator", message="本地模拟券商，仅用于 paper/rehearsal。", live_trading_enabled=False)

    def get_cash(self) -> BrokerCash:
        return BrokerCash(available_cash=self.cash, total_cash=self.cash)

    def get_account(self) -> BrokerAccountSnapshot:
        return BrokerAccountSnapshot(broker="simulator", cash=self.get_cash(), positions=[], authorized=True)

    def place_order(self, request: LiveOrderRequest) -> LiveOrderAck:
        order_id = f"sim-{len(self.orders)+1:06d}"
        order = BrokerOrder(order_id=order_id, symbol=request.symbol, side=request.side, status="accepted", quantity=request.quantity, price=request.limit_price)
        self.orders[order_id] = order
        return LiveOrderAck(True, "accepted", order_id=order_id, broker_order_id=order_id, reason="模拟券商已接收")

    def get_orders(self) -> list[BrokerOrder]:
        return list(self.orders.values())

    def query_order(self, order_id: str) -> BrokerOrder:
        return self.orders.get(order_id) or BrokerOrder(order_id=order_id, symbol="", side="", status="unknown")

    def cancel_order(self, order_id: str) -> CancelOrderResult:
        order = self.orders.get(order_id)
        if not order:
            return CancelOrderResult(False, order_id, "unknown", "订单不存在")
        order.status = "cancelled"
        return CancelOrderResult(True, order_id, "cancelled")

    def get_positions(self) -> list[BrokerPosition]:
        return []
