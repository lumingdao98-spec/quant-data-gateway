from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from typing import Any

from quant_data.chart.trading_marker_engine import TradingMarkerEngine
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
    """Live broker facade with safe defaults and persistent audit trail."""

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
        self.marker_engine = TradingMarkerEngine()
        self._store_live_session()

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
        self._store_live_session()
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
        self.session.status = "connected" if status.get("connected") else "disabled"
        self._store_live_session()
        self.audit.record("live_broker_connect", status, mode="live", session_id=self.session.session_id)
        return {"ok": status.get("connected") is True, "data": status}

    def disconnect(self) -> dict[str, Any]:
        self.broker.disconnect()
        self.session.status = "disabled"
        self._store_live_session()
        self.audit.record("live_broker_disconnect", {}, mode="live", session_id=self.session.session_id)
        return {"ok": True, "data": self.status()}

    def kill_switch(self, enabled: bool = True) -> dict[str, Any]:
        self.session.kill_switch = bool(enabled)
        self.session.status = "killed" if enabled else "disabled"
        self._store_live_session()
        self.audit.record("live_kill_switch", {"enabled": enabled}, mode="live", session_id=self.session.session_id)
        return {"ok": True, "data": self.session.to_dict()}

    def preview_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        order = self._order_from_payload(payload)
        pre = self._can_live_place(order)
        order.status = "prechecked" if pre["ok"] else "risk_blocked"
        order.status_reason = pre["reason"]
        self.store.put("orders", order.to_dict(), mode="live", symbol=order.symbol, session_id=order.session_id)
        self._store_marker(order.to_dict())
        preview = self.order_service.preview(order)
        preview["precheck"] = pre
        return preview

    def place_order(self, payload: dict[str, Any], *, confirmed: bool = False) -> dict[str, Any]:
        order = self._order_from_payload(payload)
        pre = self._can_live_place(order)
        if not pre["ok"]:
            order.status = "rejected"
            order.status_reason = pre["reason"]
            self.store.put("orders", order.to_dict(), mode="live", symbol=order.symbol, session_id=order.session_id)
            self._store_marker(order.to_dict())
            self.audit.record("live_order_rejected", order.to_dict(), mode="live", symbol=order.symbol, session_id=order.session_id)
            return {"ok": False, "data": order.to_dict(), "reason": pre["reason"]}

        if self.config.order_confirm_required and not confirmed:
            task = self.confirm_queue.enqueue(
                symbol=order.symbol,
                action=order.side,
                reason="真实订单需要人工确认",
                risk_flags=["ORDER_CONFIRM_REQUIRED"],
                payload={"order": order.to_dict(), "precheck": pre},
            )
            order.status = "needs_confirmation"
            order.status_reason = "真实订单需要人工确认"
            self.store.put("manual_confirmations", task.to_dict(), mode="live", symbol=order.symbol, session_id=order.session_id, record_id=task.task_id)
            self.store.put("orders", order.to_dict(), mode="live", symbol=order.symbol, session_id=order.session_id)
            self._store_marker(order.to_dict())
            self.audit.record("live_order_needs_confirmation", {"order": order.to_dict(), "confirmation": task.to_dict()}, mode="live", symbol=order.symbol, session_id=order.session_id)
            return {"ok": False, "data": order.to_dict(), "confirmation": task.to_dict(), "reason": "needs_confirmation"}

        result = self.order_service.place(order, confirmed=True)
        routed_order = dict(result.get("order") or order.to_dict())
        routed_order.setdefault("session_id", order.session_id)
        routed_order.setdefault("mode", "live")
        self.store.put("orders", routed_order, mode="live", symbol=order.symbol, session_id=order.session_id, record_id=str(routed_order.get("order_id") or order.order_id))
        self.store.put(
            "broker_raw_responses",
            {"order_id": order.order_id, "broker_ack": result.get("broker_ack") or {}, "result": result, "created_at": _now()},
            mode="live",
            symbol=order.symbol,
            session_id=order.session_id,
            record_id=_stable_id("broker", order.order_id, result.get("broker_ack")),
        )
        self._store_marker(routed_order)
        self.audit.record("live_order_submitted", result, mode="live", symbol=order.symbol, session_id=order.session_id)
        return {"ok": result["ok"], "data": result}

    def approve_confirmation(self, confirm_id: str) -> dict[str, Any]:
        task_before = self.confirm_queue.tasks.get(confirm_id)
        if task_before is None:
            return {"ok": False, "message": f"confirm task not found: {confirm_id}"}
        task = self.confirm_queue.approve(confirm_id, operator="user")
        self.store.put("manual_confirmations", task.to_dict(), mode="live", symbol=task.symbol, session_id=self.session.session_id, record_id=task.task_id)
        self.audit.record("live_confirmation_approved", task.to_dict(), mode="live", symbol=task.symbol, session_id=self.session.session_id)
        order_payload = dict(task_before.payload.get("order") or {})
        if not order_payload:
            return {"ok": True, "data": task.to_dict(), "execution": {"ok": False, "reason": "confirmation has no order payload"}}
        execution = self.place_order(order_payload, confirmed=True)
        return {"ok": bool(execution.get("ok")), "data": task.to_dict(), "execution": execution}

    def reject_confirmation(self, confirm_id: str) -> dict[str, Any]:
        task = self.confirm_queue.reject(confirm_id, operator="user")
        self.store.put("manual_confirmations", task.to_dict(), mode="live", symbol=task.symbol, session_id=self.session.session_id, record_id=task.task_id)
        self.audit.record("live_confirmation_rejected", task.to_dict(), mode="live", symbol=task.symbol, session_id=self.session.session_id)
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
        if self._daily_live_order_count() >= int(self.config.max_daily_live_order_count or 0):
            return {"ok": False, "reason": "当日真实订单数超过 MAX_DAILY_LIVE_ORDER_COUNT"}
        return {"ok": True, "reason": "ok"}

    def _order_from_payload(self, payload: dict[str, Any]) -> UnifiedOrder:
        data = dict(payload or {})
        req = LiveOrderRequest(**{k: v for k, v in data.items() if k in LiveOrderRequest.__dataclass_fields__})
        return UnifiedOrder(
            order_id=str(data.get("order_id") or f"live-{req.symbol}-{len(self.store.list('orders', mode='live', limit=9999))+1:06d}"),
            session_id=str(data.get("session_id") or self.session.session_id),
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
            status=str(data.get("status") or "signal_created"),
            status_reason=str(data.get("status_reason") or ""),
        )

    def _store_live_session(self) -> None:
        self.store.put("live_sessions", self.session.to_dict(), mode="live", session_id=self.session.session_id, record_id=self.session.session_id)

    def _store_marker(self, order: dict[str, Any]) -> None:
        marker = self.marker_engine.from_order(order).to_dict()
        self.store.put("chart_markers", marker, mode="live", symbol=marker.get("symbol", ""), session_id=str(order.get("session_id") or self.session.session_id), record_id=marker["marker_id"])

    def _daily_live_order_count(self) -> int:
        today = datetime.now().date().isoformat()
        rows = self.store.list("orders", mode="live", limit=5000)
        active_statuses = {"needs_confirmation", "confirmed", "submitted", "accepted", "partially_filled", "filled"}
        return sum(1 for row in rows if str(row.get("created_at") or "").startswith(today) and str(row.get("status") or "") in active_statuses)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _stable_id(*parts: Any) -> str:
    raw = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return sha256(raw.encode("utf-8")).hexdigest()[:24]
