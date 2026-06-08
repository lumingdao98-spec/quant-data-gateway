from __future__ import annotations

from typing import Any

from quant_data.persistence.trading_store import TradingStore
from quant_data.trading.audit_log_v323 import TradingAuditLogV323
from quant_data.trading.broker import (
    BrokerAdapter,
    BrokerConfig,
    DisabledBrokerAdapter,
    LiveOrderRequest,
    PTradeBrokerAdapter,
    QmtBrokerAdapter,
    SimulatorBrokerAdapter,
    load_broker_config,
)
from quant_data.trading.order_models import UnifiedOrder

from .live_confirm_queue import LiveConfirmQueue
from .live_order_service import LiveOrderService
from .live_position_sync import LivePositionSync
from .live_reconciliation import LiveReconciliation
from .live_session import LiveSession


class LiveTradingEngine:
    def __init__(self, config: BrokerConfig | None = None, broker: BrokerAdapter | None = None, store: TradingStore | None = None) -> None:
        self.config = config or load_broker_config()
        self.broker = broker or self._broker_from_config(self.config)
        self.session = LiveSession(broker=self.config.broker_type)
        self.confirm_queue = LiveConfirmQueue()
        self.order_service = LiveOrderService(self.broker)
        self.position_sync = LivePositionSync(self.broker)
        self.reconciliation = LiveReconciliation(self.broker)
        self.store = store or TradingStore()
        self.audit = TradingAuditLogV323(self.store)

    def _broker_from_config(self, config: BrokerConfig) -> BrokerAdapter:
        if config.broker_type == "qmt":
            return QmtBrokerAdapter(config)
        if config.broker_type == "ptrade":
            return PTradeBrokerAdapter(config)
        if config.broker_type == "simulator":
            return SimulatorBrokerAdapter()
        return DisabledBrokerAdapter(config)

    def status(self) -> dict[str, Any]:
        health = self.broker.health_check().to_dict()
        return {
            "ok": True,
            "session": self.session.to_dict(),
            "broker": health,
            "config": self.config.to_dict(),
            "safety": {
                "FEATURE_LIVE_BROKER": self.config.feature_live_broker,
                "LIVE_TRADING_ENABLED": self.config.live_trading_enabled,
                "ORDER_CONFIRM_REQUIRED": self.config.order_confirm_required,
                "LIVE_KILL_SWITCH": self.config.live_kill_switch or self.session.kill_switch,
            },
            "disclaimer": "研究辅助，不构成投资建议；真实交易需用户自行确认合规与风险。",
        }

    def connect(self) -> dict[str, Any]:
        status = self.broker.connect().to_dict()
        self.audit.record("live_broker_connect", status, mode="live")
        return {"ok": status.get("connected") is True, "data": status}

    def disconnect(self) -> dict[str, Any]:
        self.broker.disconnect()
        self.audit.record("live_broker_disconnect", {}, mode="live")
        return {"ok": True, "data": self.status()}

    def kill_switch(self, enabled: bool = True) -> dict[str, Any]:
        self.session.kill_switch = bool(enabled)
        self.session.status = "killed" if enabled else "disabled"
        self.audit.record("live_kill_switch", {"enabled": enabled}, mode="live")
        return {"ok": True, "data": self.session.to_dict()}

    def preview_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        order = self._order_from_payload(payload)
        if not self._can_live_place(order)["ok"]:
            order.status = "risk_blocked"
            order.status_reason = self._can_live_place(order)["reason"]
        self.store.put("orders", order.to_dict(), mode="live", symbol=order.symbol, session_id=order.session_id)
        return self.order_service.preview(order)

    def place_order(self, payload: dict[str, Any], *, confirmed: bool = False) -> dict[str, Any]:
        order = self._order_from_payload(payload)
        pre = self._can_live_place(order)
        if not pre["ok"]:
            order.status = "rejected"
            order.status_reason = pre["reason"]
            self.store.put("orders", order.to_dict(), mode="live", symbol=order.symbol, session_id=order.session_id)
            self.audit.record("live_order_rejected", order.to_dict(), mode="live", symbol=order.symbol, session_id=order.session_id)
            return {"ok": False, "data": order.to_dict(), "reason": pre["reason"]}
        if self.config.order_confirm_required and not confirmed:
            task = self.confirm_queue.enqueue(symbol=order.symbol, action=order.side, reason="真实订单需要人工确认", payload={"order": order.to_dict()})
            order.status = "needs_confirmation"
            order.status_reason = "真实订单需要人工确认"
            self.store.put("manual_confirmations", task.to_dict(), mode="live", symbol=order.symbol, session_id=order.session_id)
            self.store.put("orders", order.to_dict(), mode="live", symbol=order.symbol, session_id=order.session_id)
            return {"ok": False, "data": order.to_dict(), "confirmation": task.to_dict(), "reason": "needs_confirmation"}
        result = self.order_service.place(order, confirmed=True)
        self.store.put("orders", result["order"], mode="live", symbol=order.symbol, session_id=order.session_id)
        return {"ok": result["ok"], "data": result}

    def approve_confirmation(self, confirm_id: str) -> dict[str, Any]:
        task = self.confirm_queue.approve(confirm_id, operator="user")
        return {"ok": True, "data": task.to_dict()}

    def reject_confirmation(self, confirm_id: str) -> dict[str, Any]:
        task = self.confirm_queue.reject(confirm_id, operator="user")
        return {"ok": True, "data": task.to_dict()}

    def _can_live_place(self, order: UnifiedOrder) -> dict[str, Any]:
        if self.session.kill_switch or self.config.live_kill_switch:
            return {"ok": False, "reason": "LIVE_KILL_SWITCH 已开启"}
        if not (self.config.feature_live_broker and self.config.live_trading_enabled):
            return {"ok": False, "reason": "FEATURE_LIVE_BROKER/LIVE_TRADING_ENABLED 未开启"}
        if self.config.trade_whitelist_symbols and order.symbol not in self.config.trade_whitelist_symbols:
            return {"ok": False, "reason": "标的不在 TRADE_WHITELIST_SYMBOLS"}
        value = abs((order.limit_price or 0.0) * order.quantity)
        if value > self.config.max_live_order_value:
            return {"ok": False, "reason": "订单金额超过 MAX_LIVE_ORDER_VALUE"}
        return {"ok": True, "reason": "ok"}

    def _order_from_payload(self, payload: dict[str, Any]) -> UnifiedOrder:
        req = LiveOrderRequest(**{k: v for k, v in dict(payload or {}).items() if k in LiveOrderRequest.__dataclass_fields__})
        return UnifiedOrder(
            order_id=str(payload.get("order_id") or f"live-{req.symbol}-{len(self.store.list('orders', mode='live', limit=9999))+1:06d}"),
            session_id=self.session.session_id,
            mode="live",
            symbol=req.symbol,
            side=req.side,
            order_type=req.order_type,
            quantity=int(req.quantity or 0),
            limit_price=req.limit_price,
            target_weight=req.target_weight,
            signal_id=req.signal_id,
            provenance_id=req.provenance_id,
            risk_check_id=req.risk_check_id,
            source_page=req.source_page,
            strategy_family=req.strategy_family,
        )
