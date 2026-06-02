from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from .audit_log import AuditLog
from .paper_account import PaperAccount, PaperFill


@dataclass(slots=True)
class ManagedOrder:
    order_id: str
    symbol: str
    side: str
    quantity: int
    price: float
    target_weight: float = 0.0
    order_type: str = "market"
    status: str = "pending"
    reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    filled_quantity: int = 0
    avg_fill_price: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OrderManager:
    def __init__(self, account: PaperAccount, audit_log: AuditLog | None = None) -> None:
        self.account = account
        self.audit_log = audit_log or AuditLog()
        self.orders: list[ManagedOrder] = []

    def build_order(
        self,
        *,
        symbol: str,
        target_weight: float,
        side: str,
        price: float,
        order_type: str = "market",
        reason: str = "",
        lot_size: int = 100,
    ) -> ManagedOrder:
        equity = max(self.account.equity, 1.0)
        current = self.account.positions.get(symbol)
        current_value = current.market_value if current else 0.0
        target_value = max(0.0, float(target_weight or 0.0) * equity)
        raw_value = target_value - current_value if side in {"buy", "add"} else current_value - target_value
        if side == "sell":
            raw_value = current_value
        qty = int(max(0.0, raw_value) / max(float(price or 0.0), 0.0001))
        lot = max(1, int(lot_size or 1))
        qty = int(qty // lot) * lot
        order = ManagedOrder(
            order_id=f"po-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}",
            symbol=symbol,
            side="buy" if side in {"buy", "add"} else "sell",
            quantity=qty,
            price=float(price or 0.0),
            target_weight=float(target_weight or 0.0),
            order_type=order_type,
            reason=reason,
        )
        self.orders.append(order)
        self.audit_log.record("order_created", order.to_dict())
        return order

    def reject(self, order: ManagedOrder, reason: str) -> ManagedOrder:
        order.status = "rejected"
        order.reason = reason or order.reason
        order.updated_at = datetime.now().isoformat(timespec="seconds")
        self.audit_log.record("order_rejected", order.to_dict())
        return order

    def submit(self, order: ManagedOrder) -> ManagedOrder:
        order.status = "submitted"
        order.updated_at = datetime.now().isoformat(timespec="seconds")
        self.audit_log.record("order_submitted", order.to_dict())
        return order

    def simulate_fill(
        self,
        order: ManagedOrder,
        *,
        fill_price: float | None = None,
        fill_ratio: float = 1.0,
        fee_rate: float = 0.0003,
        slippage_rate: float = 0.0005,
    ) -> ManagedOrder:
        if order.status in {"rejected", "cancelled", "expired"}:
            return order
        self.submit(order)
        qty = int(order.quantity * max(0.0, min(1.0, fill_ratio)))
        if qty <= 0:
            return self.reject(order, "数量为0，无法模拟成交")
        price = float(fill_price or order.price)
        amount = qty * price
        fill = PaperFill(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=qty,
            price=price,
            amount=amount,
            fee=amount * fee_rate,
            slippage=amount * slippage_rate,
        )
        self.account.apply_fill(fill)
        order.filled_quantity = qty
        order.avg_fill_price = price
        order.status = "filled" if qty >= order.quantity else "partial"
        order.updated_at = datetime.now().isoformat(timespec="seconds")
        self.audit_log.record("order_filled", {**order.to_dict(), "fill": fill.to_dict(), "account": self.account.snapshot()})
        return order

    def list_orders(self, limit: int = 200) -> list[dict[str, Any]]:
        return [x.to_dict() for x in self.orders[-max(1, int(limit or 200)) :]][::-1]
