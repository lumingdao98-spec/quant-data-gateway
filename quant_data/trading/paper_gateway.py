from __future__ import annotations

from uuid import uuid4

from .audit_log import AuditLog
from .models import PaperOrder, PaperPosition, TradingSignal
from .risk_gateway import RiskGateway
from .signal_queue import SignalQueue


class PaperTradingGateway:
    def __init__(self, *, initial_cash: float = 100_000.0, risk_gateway: RiskGateway | None = None) -> None:
        self.cash = float(initial_cash)
        self.positions: dict[str, PaperPosition] = {}
        self.orders: list[PaperOrder] = []
        self.risk_gateway = risk_gateway or RiskGateway()
        self.audit = AuditLog()
        self.signals = SignalQueue()

    @property
    def equity(self) -> float:
        return self.cash + sum(p.market_value for p in self.positions.values())

    def submit_signal(self, signal: TradingSignal, quote: dict | None = None) -> dict:
        self.signals.push(signal)
        risk = self.risk_gateway.check(signal, cash=self.cash, equity=max(self.equity, self.cash), positions=self.positions, quote=quote)
        order = None
        if risk.allowed:
            quantity = int(signal.quantity or 0)
            price = signal.price
            order = PaperOrder(
                order_id=f"paper-{uuid4().hex[:10]}",
                symbol=signal.symbol,
                side=signal.side,
                quantity=quantity,
                price=price,
                status="accepted" if not risk.require_human_confirmation else "needs_confirmation",
                reason=signal.reason,
            )
            self.orders.append(order)
        self.audit.record("signal_received", {"signal": signal.to_dict(), "risk": risk.to_dict(), "order": order.to_dict() if order else None})
        return {"risk": risk.to_dict(), "order": order.to_dict() if order else None}

    def orders_snapshot(self) -> list[dict]:
        return [x.to_dict() for x in self.orders]

    def positions_snapshot(self) -> dict:
        return {
            "cash": round(self.cash, 6),
            "equity": round(self.equity, 6),
            "positions": {k: v.to_dict() for k, v in self.positions.items()},
            "paper_only": True,
        }
