from __future__ import annotations

from typing import Any

from .order_models import ORDER_STATUSES, UnifiedOrder
from .order_state_machine import OrderStateMachine


class OrderLifecycle:
    def __init__(self) -> None:
        self.state_machine = OrderStateMachine()

    def transition(self, order: UnifiedOrder, status: str, reason: str = "", **timestamps: Any) -> UnifiedOrder:
        if status not in ORDER_STATUSES:
            status = "unknown"
            reason = reason or "未知订单状态"
        at = str(
            timestamps.get("submitted_at")
            or timestamps.get("filled_at")
            or timestamps.get("cancelled_at")
            or timestamps.get("canceled_at")
            or ""
        )
        self.state_machine.transition(order, status, reason, strict=False, at=at)
        return order

    def precheck(
        self,
        order: UnifiedOrder,
        *,
        data_fresh: bool = True,
        provenance_exists: bool = True,
        risk_approved: bool = True,
    ) -> UnifiedOrder:
        if not data_fresh:
            return self.transition(order, "risk_blocked", "数据过期或缺失")
        if not provenance_exists:
            return self.transition(order, "risk_blocked", "评分溯源缺失")
        if not risk_approved:
            return self.transition(order, "risk_blocked", "风控未通过")
        return self.transition(order, "prechecked", "预检查通过")
