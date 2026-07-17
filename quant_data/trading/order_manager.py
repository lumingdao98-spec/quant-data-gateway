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
    requested_value: float = 0.0
    minimum_lot_value: float = 0.0
    minimum_account_equity: float = 0.0
    sizing_status: str = "executable"

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
        sizing = self.preview_order(
            symbol=symbol,
            target_weight=target_weight,
            side=side,
            price=price,
            lot_size=lot_size,
        )
        qty = int(sizing["quantity"])
        sizing_reason = str(sizing.get("message") or "")
        order = ManagedOrder(
            order_id=f"po-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}",
            symbol=symbol,
            side="buy" if side in {"buy", "add"} else "sell",
            quantity=qty,
            price=float(price or 0.0),
            target_weight=float(target_weight or 0.0),
            order_type=order_type,
            reason="；".join(x for x in (reason, sizing_reason) if x),
            requested_value=float(sizing["requested_value"]),
            minimum_lot_value=float(sizing["minimum_lot_value"]),
            minimum_account_equity=float(sizing["minimum_account_equity"]),
            sizing_status=str(sizing["status"]),
        )
        self.orders.append(order)
        self.audit_log.record("order_created", order.to_dict())
        return order

    def preview_order(
        self,
        *,
        symbol: str,
        target_weight: float,
        side: str,
        price: float,
        lot_size: int = 100,
    ) -> dict[str, Any]:
        equity = max(self.account.equity, 1.0)
        current = self.account.positions.get(symbol)
        current_value = current.market_value if current else 0.0
        target_value = max(0.0, float(target_weight or 0.0) * equity)
        raw_value = target_value - current_value if side in {"buy", "add"} else current_value - target_value
        if side == "sell":
            raw_value = current_value
        px = max(float(price or 0.0), 0.0001)
        lot = max(1, int(lot_size or 1))
        raw_quantity = int(max(0.0, raw_value) / px)
        quantity = int(raw_quantity // lot) * lot
        minimum_lot_value = px * lot
        weight = max(0.0, float(target_weight or 0.0))
        minimum_account_equity = minimum_lot_value / weight if side in {"buy", "add"} and weight > 0 else 0.0
        status = "executable" if quantity > 0 else "below_minimum_lot"
        message = ""
        if status != "executable":
            message = (
                f"目标仓位{weight * 100:.2f}%对应约{raw_quantity}股，低于A股最小买入{lot}股；"
                f"按当前价格至少需要{minimum_lot_value:.2f}元，维持该仓位上限时账户权益需约{minimum_account_equity:.2f}元"
            )
        return {
            "symbol": symbol,
            "side": "buy" if side in {"buy", "add"} else "sell",
            "target_weight": weight,
            "requested_value": round(max(0.0, raw_value), 6),
            "raw_quantity": raw_quantity,
            "quantity": quantity,
            "lot_size": lot,
            "minimum_lot_value": round(minimum_lot_value, 6),
            "minimum_account_equity": round(minimum_account_equity, 6),
            "status": status,
            "message": message,
        }

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
