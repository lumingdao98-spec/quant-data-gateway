from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from typing import Any

from quant_data.chart.trading_marker_engine import TradingMarkerEngine
from quant_data.market_calendar import MarketCalendar
from quant_data.persistence.trading_store import TradingStore
from quant_data.strategy.strategy_family import get_strategy_execution_profile, normalize_strategy_family
from quant_data.trading.audit_log_v323 import TradingAuditLogV323
from quant_data.trading.broker import (
    BrokerAdapter,
    BrokerConfig,
    DisabledBrokerAdapter,
    HttpBridgeBrokerAdapter,
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
from .live_sync_service import LiveSyncService


def market_session_status() -> dict[str, Any]:
    """Compatibility seam backed by the configured market calendar."""
    session = MarketCalendar().session("CN")
    return {
        **session,
        "is_trading_time": bool(session.get("is_trading")),
    }


class LiveTradingEngine:
    """Live broker facade with safe defaults and persistent audit trail."""

    def __init__(self, config: BrokerConfig | None = None, broker: BrokerAdapter | None = None, store: TradingStore | None = None) -> None:
        self.config = config or load_broker_config()
        self.broker = broker or self._broker_from_config(self.config)
        self.session = LiveSession(broker=self.config.broker_type)
        self.confirm_queue = LiveConfirmQueue()
        self.order_service = LiveOrderService(self.broker)
        self.store = store or TradingStore()
        self.sync_service = LiveSyncService(self.broker, self.store)
        self.position_sync = LivePositionSync(self.broker)
        self.reconciliation = LiveReconciliation(self.broker, self.store)
        self.audit = TradingAuditLogV323(self.store)
        self.marker_engine = TradingMarkerEngine()
        self._store_live_session()

    def _broker_from_config(self, config: BrokerConfig) -> BrokerAdapter:
        if config.broker_type == "qmt":
            return QmtBrokerAdapter(config)
        if config.broker_type == "ptrade":
            return PTradeBrokerAdapter(config)
        if config.broker_type == "http_bridge":
            return HttpBridgeBrokerAdapter(config)
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
        pre = self._can_live_place(order, payload=payload, require_broker=False)
        order.status = "prechecked" if pre["ok"] else "risk_blocked"
        order.status_reason = pre["reason"]
        stored_order = {
            **order.to_dict(),
            "record_stage": "precheck" if pre["ok"] else "risk_blocked",
            "broker_submitted": False,
        }
        self.store.put("orders", stored_order, mode="live", symbol=order.symbol, session_id=order.session_id)
        self._store_marker(order.to_dict())
        preview = self.order_service.preview(order)
        preview["precheck"] = pre
        preview["record_stage"] = stored_order["record_stage"]
        preview["broker_submitted"] = False
        return preview

    def preview_orders_batch(self, payload: dict[str, Any], symbols: list[str]) -> dict[str, Any]:
        rows = []
        for symbol in _unique_symbols(symbols)[:50]:
            rows.append({"symbol": symbol, "preview": self.preview_order({**payload, "symbol": symbol})})
        return {
            "ok": bool(rows),
            "data": rows,
            "count": len(rows),
            "safety": "每笔订单独立经过数据、评分、风控、白名单和确认队列检查。",
            "note": "批量预检查不会绕过 LIVE_TRADING_ENABLED、kill switch 或人工确认。",
        }

    def place_order(self, payload: dict[str, Any], *, confirmed: bool = False) -> dict[str, Any]:
        order = self._order_from_payload(payload)
        pre = self._can_live_place(order, payload=payload, require_broker=confirmed)
        if not pre["ok"]:
            order.status = "rejected"
            order.status_reason = pre["reason"]
            stored_order = {
                **order.to_dict(),
                "record_stage": "risk_blocked",
                "broker_submitted": False,
                "precheck": pre,
            }
            self.store.put("orders", stored_order, mode="live", symbol=order.symbol, session_id=order.session_id)
            self._store_marker(order.to_dict())
            self.audit.record("live_order_rejected", order.to_dict(), mode="live", symbol=order.symbol, session_id=order.session_id)
            return {"ok": False, "data": stored_order, "reason": pre["reason"]}

        if self.config.order_confirm_required and not confirmed:
            task = self.confirm_queue.enqueue(
                symbol=order.symbol,
                action=order.side,
                reason="真实订单需要人工确认",
                risk_flags=["ORDER_CONFIRM_REQUIRED"],
                payload={
                    "order": order.to_dict(),
                    "precheck": pre,
                    "safety_context": self._safety_context(payload),
                },
            )
            order.status = "needs_confirmation"
            order.status_reason = "真实订单需要人工确认"
            self.store.put("manual_confirmations", task.to_dict(), mode="live", symbol=order.symbol, session_id=order.session_id, record_id=task.task_id)
            stored_order = {**order.to_dict(), "record_stage": "confirmation", "broker_submitted": False}
            self.store.put("orders", stored_order, mode="live", symbol=order.symbol, session_id=order.session_id)
            self._store_marker(order.to_dict())
            self.audit.record("live_order_needs_confirmation", {"order": order.to_dict(), "confirmation": task.to_dict()}, mode="live", symbol=order.symbol, session_id=order.session_id)
            return {"ok": False, "data": stored_order, "confirmation": task.to_dict(), "reason": "needs_confirmation"}

        result = self.order_service.place(order, confirmed=True)
        routed_order = dict(result.get("order") or order.to_dict())
        routed_order.setdefault("session_id", order.session_id)
        routed_order.setdefault("mode", "live")
        routed_order["record_stage"] = "broker_submission"
        routed_order["broker_submitted"] = True
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

    def place_orders_batch(self, payload: dict[str, Any], symbols: list[str], *, confirmed: bool = False) -> dict[str, Any]:
        rows = []
        for symbol in _unique_symbols(symbols)[:50]:
            rows.append({"symbol": symbol, "result": self.place_order({**payload, "symbol": symbol}, confirmed=confirmed)})
        return {
            "ok": bool(rows) and all(bool((row.get("result") or {}).get("ok")) for row in rows),
            "data": rows,
            "count": len(rows),
            "safety": "批量入口不会绕过逐笔风控、人工确认或全局 kill switch。",
            "note": "真实批量下单不会绕过逐笔风控、白名单、确认队列和券商适配器。",
        }

    def sync_live_account_state(self, *, force: bool = False) -> dict[str, Any]:
        result = self.sync_service.sync(session_id=self.session.session_id, force=force)
        self.audit.record(
            "live_broker_sync",
            {
                "ok": result.get("ok"),
                "quality_status": result.get("quality_status"),
                "positions": len(result.get("positions") or []),
                "orders": len(result.get("orders") or []),
                "trades": len(result.get("trades") or []),
                "missing_reasons": result.get("missing_reasons") or [],
                "fetched_at": result.get("fetched_at"),
            },
            mode="live",
            session_id=self.session.session_id,
        )
        return result

    def reconcile(self) -> dict[str, Any]:
        self.sync_live_account_state(force=True)
        result = self.reconciliation.daily_check(session_id=self.session.session_id)
        self.audit.record("live_reconciliation", result, mode="live", session_id=self.session.session_id)
        return result

    def approve_confirmation(self, confirm_id: str) -> dict[str, Any]:
        task_before = self.confirm_queue.tasks.get(confirm_id)
        if task_before is None:
            return {"ok": False, "message": f"confirm task not found: {confirm_id}"}
        task = self.confirm_queue.approve(confirm_id, operator="user")
        self.store.put("manual_confirmations", task.to_dict(), mode="live", symbol=task.symbol, session_id=self.session.session_id, record_id=task.task_id)
        self.audit.record("live_confirmation_approved", task.to_dict(), mode="live", symbol=task.symbol, session_id=self.session.session_id)
        order_payload = {
            **dict(task_before.payload.get("order") or {}),
            **dict(task_before.payload.get("safety_context") or {}),
        }
        if not order_payload:
            return {"ok": True, "data": task.to_dict(), "execution": {"ok": False, "reason": "confirmation has no order payload"}}
        execution = self.place_order(order_payload, confirmed=True)
        stored_task = {**task.to_dict(), "execution": execution}
        self.store.put(
            "manual_confirmations",
            stored_task,
            mode="live",
            symbol=task.symbol,
            session_id=self.session.session_id,
            record_id=task.task_id,
        )
        return {"ok": bool(execution.get("ok")), "data": stored_task, "execution": execution}

    def reject_confirmation(self, confirm_id: str) -> dict[str, Any]:
        task = self.confirm_queue.reject(confirm_id, operator="user")
        self.store.put("manual_confirmations", task.to_dict(), mode="live", symbol=task.symbol, session_id=self.session.session_id, record_id=task.task_id)
        self.audit.record("live_confirmation_rejected", task.to_dict(), mode="live", symbol=task.symbol, session_id=self.session.session_id)
        return {"ok": True, "data": task.to_dict()}

    def _can_live_place_legacy(self, order: UnifiedOrder) -> dict[str, Any]:
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

    def _can_live_place(
        self,
        order: UnifiedOrder,
        *,
        payload: dict[str, Any] | None = None,
        require_broker: bool = False,
    ) -> dict[str, Any]:
        """Evaluate live-order gates without trusting browser-only flags.

        Simulator orders keep the rehearsal path. Real broker adapters must
        reference persisted provenance and risk checks, and every gate is
        evaluated again immediately before broker submission.
        """

        context = dict(payload or {})
        gates: list[dict[str, Any]] = []

        def gate(key: str, passed: bool, reason: str, *, required: bool = True) -> None:
            gates.append({"gate_key": key, "passed": bool(passed), "required": required, "reason": reason})

        gate("valid_symbol", len(order.symbol) == 6 and order.symbol.isdigit(), "标的代码必须是 6 位数字")
        gate("valid_side", str(order.side or "").lower() in {"buy", "sell"}, "订单方向必须是 buy 或 sell")
        gate("valid_quantity", int(order.quantity or 0) > 0, "订单股数必须大于 0")
        gate(
            "valid_limit_price",
            order.order_type != "limit" or float(order.limit_price or 0) > 0,
            "限价单必须提供大于 0 的限价",
        )
        gate(
            "kill_switch",
            not (self.session.kill_switch or self.config.live_kill_switch),
            "LIVE_KILL_SWITCH 已开启",
        )
        gate(
            "live_flags",
            bool(self.config.feature_live_broker and self.config.live_trading_enabled),
            "真实交易功能尚未显式开启",
        )
        gate(
            "symbol_whitelist",
            not self.config.trade_whitelist_symbols or order.symbol in self.config.trade_whitelist_symbols,
            "标的不在实盘白名单",
        )

        price = self._reference_price(order, context)
        gate("reference_price", price > 0, "缺少可核验的委托参考价格")
        value = abs(price * int(order.quantity or 0))
        gate(
            "max_order_value",
            value <= float(self.config.max_live_order_value or 0),
            "订单金额超过单笔实盘上限",
        )
        daily_limit = int(self.config.max_daily_live_order_count or 0)
        gate(
            "daily_order_count",
            daily_limit > 0 and self._daily_live_order_count() < daily_limit,
            "当日真实委托数量达到上限",
        )

        if any(row["required"] and not row["passed"] for row in gates):
            return self._precheck_result(gates, order_value=value)

        real_provider = self.config.broker_type in {"qmt", "ptrade", "http_bridge"}
        if real_provider:
            provenance = self.store.get("score_provenance", order.provenance_id) if order.provenance_id else None
            provenance_ok = bool(provenance) and str((provenance or {}).get("symbol") or "") == order.symbol
            gate("score_provenance", provenance_ok, "缺少与该标的一致的持久化评分溯源")
            provenance_fresh = provenance_ok and not list((provenance or {}).get("stale_data") or [])
            gate(
                "score_provenance_fresh",
                provenance_fresh,
                "评分溯源包含过期数据",
                required=order.side == "buy",
            )

            risk_check = self.store.get("risk_checks", order.risk_check_id) if order.risk_check_id else None
            risk_order = (risk_check or {}).get("order") if isinstance((risk_check or {}).get("order"), dict) else {}
            risk_matches = (
                str((risk_check or {}).get("symbol") or risk_order.get("symbol") or "") == order.symbol
                and str((risk_check or {}).get("mode") or "") == "live"
                and str(risk_order.get("side") or "").lower() == order.side
                and int(float(risk_order.get("quantity") or 0)) == int(order.quantity or 0)
            )
            risk_ok = bool(risk_check) and risk_matches and bool(
                (risk_check or {}).get("approved", (risk_check or {}).get("allowed"))
            )
            gate("risk_approved", risk_ok, "缺少已通过且已落库的风控检查")

            freshness = context.get("data_freshness") if isinstance(context.get("data_freshness"), dict) else {}
            quote = context.get("quote") if isinstance(context.get("quote"), dict) else {}
            quote_at = quote.get("fetched_at") or quote.get("ts") or context.get("quote_fetched_at")
            freshness_ok = self._freshness_context_ok(freshness, quote_at)
            gate(
                "fresh_market_data",
                freshness_ok,
                "关键行情快照缺失或已过期",
                required=order.side == "buy",
            )
            quote_traceable = bool(quote.get("source") or quote.get("source_id")) and bool(
                quote.get("fetched_at") or quote.get("ts") or context.get("quote_fetched_at")
            )
            gate("traceable_quote", quote_traceable, "行情缺少来源或抓取时间")
            gate(
                "major_negative_veto",
                order.side != "buy" or not bool(context.get("major_negative_news") or context.get("info_negative_veto")),
                "重大负面信息阻断新增实盘仓位",
            )
            session = market_session_status()
            gate(
                "market_session",
                bool(session.get("is_trading_day") and session.get("is_trading_time")),
                "当前不是 A 股连续交易时段",
            )

        broker_connected = True
        if require_broker:
            try:
                broker_health = self.broker.health_check().to_dict()
                broker_connected = broker_health.get("connected") is True
                broker_reason = str(broker_health.get("message") or broker_health.get("status") or "券商未连接")
            except Exception as exc:
                broker_connected = False
                broker_reason = f"券商健康检查失败: {str(exc)[:160]}"
            gate("broker_connected", broker_connected, broker_reason)

        if require_broker and broker_connected:
            gate(
                "duplicate_order",
                not self._has_duplicate_active_order(order),
                "存在同标的同方向的活动委托",
            )
            try:
                cash = self.broker.get_cash()
                gate(
                    "available_cash",
                    order.side != "buy" or float(cash.available_cash or 0) >= value,
                    "券商可用资金不足",
                )
            except Exception as exc:
                gate("available_cash", False, f"无法核验券商可用资金: {str(exc)[:160]}")

            if order.side == "sell":
                try:
                    positions = self.broker.get_positions()
                    available = sum(
                        int(position.available_quantity or 0)
                        for position in positions
                        if str(position.symbol or "") == order.symbol
                    )
                    gate("available_position", available >= int(order.quantity or 0), "可卖持仓股数不足")
                except Exception as exc:
                    gate("available_position", False, f"无法核验可卖持仓: {str(exc)[:160]}")

        return self._precheck_result(gates, order_value=value)

    @staticmethod
    def _reference_price(order: UnifiedOrder, payload: dict[str, Any]) -> float:
        quote = payload.get("quote") if isinstance(payload.get("quote"), dict) else {}
        for value in (
            order.limit_price,
            payload.get("reference_price"),
            payload.get("price"),
            quote.get("last"),
            quote.get("price"),
        ):
            try:
                number = float(value or 0)
            except (TypeError, ValueError):
                continue
            if number > 0:
                return number
        return 0.0

    @staticmethod
    def _freshness_context_ok(freshness: dict[str, Any], quote_at: Any, *, ttl_seconds: int = 30) -> bool:
        if not bool(freshness.get("fresh")) or bool(freshness.get("stale")):
            return False
        if str(freshness.get("action") or "allow") != "allow" or not quote_at:
            return False
        try:
            fetched = datetime.fromisoformat(str(quote_at).replace("Z", "+00:00"))
            current = datetime.now(fetched.tzinfo) if fetched.tzinfo else datetime.now()
            age = (current - fetched).total_seconds()
        except (TypeError, ValueError):
            return False
        return -5 <= age <= max(1, int(ttl_seconds))

    @staticmethod
    def _precheck_result(gates: list[dict[str, Any]], *, order_value: float) -> dict[str, Any]:
        failed = [row for row in gates if row.get("required") and not row.get("passed")]
        return {
            "ok": not failed,
            "reason": "ok" if not failed else str(failed[0].get("reason") or failed[0].get("gate_key") or "precheck_failed"),
            "reason_code": "ok" if not failed else str(failed[0].get("gate_key") or "precheck_failed"),
            "gates": gates,
            "order_value": round(float(order_value or 0), 4),
            "failed_count": len(failed),
        }

    @staticmethod
    def _safety_context(payload: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "quote",
            "quote_fetched_at",
            "data_freshness",
            "major_negative_news",
            "info_negative_veto",
            "market_event_context",
            "signal_score",
            "risk_approved",
        }
        return {key: payload.get(key) for key in allowed if key in payload}

    def _has_duplicate_active_order(self, order: UnifiedOrder) -> bool:
        active_statuses = {"confirmed", "submitted", "accepted", "partially_filled", "cancel_requested"}
        for row in self.store.list("orders", mode="live", symbol=order.symbol, limit=500):
            if str(row.get("order_id") or "") == order.order_id:
                continue
            if str(row.get("side") or "").lower() != str(order.side or "").lower():
                continue
            if str(row.get("status") or "") in active_statuses and bool(row.get("broker_submitted", True)):
                return True
        return False

    def _order_from_payload(self, payload: dict[str, Any]) -> UnifiedOrder:
        data = dict(payload or {})
        req = LiveOrderRequest(**{k: v for k, v in data.items() if k in LiveOrderRequest.__dataclass_fields__})
        family = normalize_strategy_family(req.strategy_family or data.get("strategy") or "core_satellite")
        profile = get_strategy_execution_profile(family)
        return UnifiedOrder(
            order_id=str(data.get("order_id") or f"live-{req.symbol}-{len(self.store.list('orders', mode='live', limit=9999))+1:06d}"),
            session_id=str(data.get("session_id") or self.session.session_id),
            mode="live",
            symbol=req.symbol,
            side=str(req.side or "").lower(),
            order_type=str(req.order_type or "limit").lower(),
            quantity=int(req.quantity or 0),
            limit_price=req.limit_price,
            target_weight=req.target_weight,
            signal_id=req.signal_id,
            provenance_id=req.provenance_id,
            risk_check_id=req.risk_check_id,
            source_page=req.source_page,
            strategy_family=family,
            strategy_profile_hash=str(data.get("strategy_profile_hash") or profile.profile_hash),
            policy_hash=str(data.get("policy_hash") or profile.policy_hash),
            execution_profile_version=str(data.get("execution_profile_version") or profile.profile_version),
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
        active_statuses = {"confirmed", "submitted", "accepted", "partially_filled", "filled"}
        return sum(1 for row in rows if str(row.get("created_at") or "").startswith(today) and str(row.get("status") or "") in active_statuses)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _stable_id(*parts: Any) -> str:
    raw = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return sha256(raw.encode("utf-8")).hexdigest()[:24]


def _unique_symbols(symbols: list[str]) -> list[str]:
    out: list[str] = []
    for value in symbols or []:
        symbol = "".join(ch for ch in str(value or "") if ch.isdigit()).zfill(6)[-6:]
        if symbol and symbol not in out:
            out.append(symbol)
    return out
