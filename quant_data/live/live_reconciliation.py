from __future__ import annotations

from datetime import datetime
from typing import Any

from quant_data.persistence.trading_store import TradingStore
from quant_data.trading.broker import BrokerAdapter, DisabledBrokerAdapter


class LiveReconciliation:
    def __init__(self, broker: BrokerAdapter | None = None, store: TradingStore | None = None) -> None:
        self.broker = broker or DisabledBrokerAdapter()
        self.store = store

    def daily_check(self, *, session_id: str = "") -> dict[str, Any]:
        status = self.broker.health_check().to_dict()
        broker_orders = [x.to_dict() for x in self.broker.get_orders()]
        broker_trades = [x.to_dict() for x in self.broker.get_trades()]
        stored_orders = self.store.list_normalized("broker_orders", session_id=session_id, limit=5000) if self.store else []
        stored_trades = self.store.list_normalized("broker_trades", session_id=session_id, limit=5000) if self.store else []
        broker_order_ids = {str(x.get("broker_order_id") or x.get("order_id") or "") for x in broker_orders}
        stored_order_ids = {str(x.get("broker_order_id") or x.get("order_id") or "") for x in stored_orders}
        broker_trade_ids = {str(x.get("broker_trade_id") or x.get("trade_id") or "") for x in broker_trades}
        stored_trade_ids = {str(x.get("broker_trade_id") or x.get("trade_id") or "") for x in stored_trades}
        differences = {
            "orders_missing_locally": sorted(broker_order_ids - stored_order_ids),
            "orders_missing_at_broker": sorted(stored_order_ids - broker_order_ids),
            "trades_missing_locally": sorted(broker_trade_ids - stored_trade_ids),
            "trades_missing_at_broker": sorted(stored_trade_ids - broker_trade_ids),
        }
        ok = bool(status.get("connected")) and not any(differences.values())
        return {
            "ok": ok,
            "status": status,
            "orders": broker_orders,
            "trades": broker_trades,
            "differences": differences,
            "checked_at": datetime.now().isoformat(timespec="seconds"),
            "message": "对账一致" if ok else ("券商未连接或未授权" if not status.get("connected") else "发现本地与券商记录差异"),
        }
