from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .order_models import ORDER_STATUSES, UnifiedOrder


STATE_ALIASES = {"canceled": "cancelled"}

ALLOWED_TRANSITIONS = {
    "signal_created": {"prechecked", "risk_blocked", "rejected", "failed", "expired"},
    "prechecked": {"needs_confirmation", "confirmed", "submitted", "risk_blocked", "rejected", "expired", "failed"},
    "risk_blocked": {"prechecked", "rejected", "expired"},
    "needs_confirmation": {"confirmed", "rejected", "expired", "cancelled"},
    "confirmed": {"submitted", "rejected", "failed", "cancelled"},
    "submitted": {"accepted", "partially_filled", "filled", "cancel_requested", "rejected", "failed", "unknown"},
    "accepted": {"partially_filled", "filled", "cancel_requested", "cancelled", "rejected", "failed", "unknown"},
    "partially_filled": {"partially_filled", "filled", "cancel_requested", "cancelled", "failed", "unknown"},
    "cancel_requested": {"cancelled", "partially_filled", "filled", "rejected", "failed", "unknown"},
    "unknown": {"accepted", "partially_filled", "filled", "cancelled", "rejected", "failed", "reconciled"},
    "filled": {"reconciled"},
    "cancelled": {"reconciled"},
    "rejected": {"reconciled"},
    "failed": {"reconciled"},
    "expired": {"reconciled"},
    "reconciled": set(),
}


@dataclass(frozen=True, slots=True)
class OrderTransition:
    order_id: str
    from_status: str
    to_status: str
    reason: str
    transitioned_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "reason": self.reason,
            "transitioned_at": self.transitioned_at,
        }


class OrderStateMachine:
    def normalize(self, status: str) -> str:
        normalized = STATE_ALIASES.get(str(status or "").strip().lower(), str(status or "").strip().lower())
        return normalized if normalized in ORDER_STATUSES else "unknown"

    def can_transition(self, current: str, target: str) -> bool:
        current_status = self.normalize(current)
        target_status = self.normalize(target)
        return current_status == target_status or target_status in ALLOWED_TRANSITIONS.get(current_status, set())

    def transition(self, order: UnifiedOrder, target: str, reason: str = "", *, strict: bool = True, at: str = "") -> OrderTransition:
        current = self.normalize(order.status)
        target_status = self.normalize(target)
        if strict and not self.can_transition(current, target_status):
            raise ValueError(f"invalid order transition: {current} -> {target_status}")
        transitioned_at = at or datetime.now().isoformat(timespec="seconds")
        order.status = target_status
        order.status_reason = reason or order.status_reason
        order.updated_at = transitioned_at
        if target_status == "submitted" and not order.submitted_at:
            order.submitted_at = transitioned_at
        if target_status in {"partially_filled", "filled"}:
            order.filled_at = transitioned_at
        if target_status == "cancelled":
            order.cancelled_at = transitioned_at
        return OrderTransition(order.order_id, current, target_status, reason, transitioned_at)
