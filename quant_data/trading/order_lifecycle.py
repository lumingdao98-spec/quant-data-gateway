from __future__ import annotations

from datetime import datetime
from typing import Any

from .order_models import ORDER_STATUSES, UnifiedOrder


class OrderLifecycle:
    def transition(self, order: UnifiedOrder, status: str, reason: str = "", **timestamps: Any) -> UnifiedOrder:
        if status not in ORDER_STATUSES:
            status = "unknown"
            reason = reason or "未知订单状态"
        now = datetime.now().isoformat(timespec="seconds")
        order.status = status
        order.status_reason = reason or order.status_reason
        order.updated_at = now
        if status == "submitted":
            order.submitted_at = timestamps.get("submitted_at") or now
        elif status in {"filled", "partially_filled"}:
            order.filled_at = timestamps.get("filled_at") or now
        elif status == "cancelled":
            order.cancelled_at = timestamps.get("cancelled_at") or now
        return order

    def precheck(self, order: UnifiedOrder, *, data_fresh: bool = True, provenance_exists: bool = True, risk_approved: bool = True) -> UnifiedOrder:
        if not data_fresh:
            return self.transition(order, "risk_blocked", "数据过期或缺失")
        if not provenance_exists:
            return self.transition(order, "risk_blocked", "评分溯源缺失")
        if not risk_approved:
            return self.transition(order, "risk_blocked", "风控未通过")
        return self.transition(order, "prechecked", "预检查通过")
