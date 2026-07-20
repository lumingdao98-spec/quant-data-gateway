from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
import time
from typing import Any

from quant_data.chart.trading_marker_engine import TradingMarkerEngine
from quant_data.persistence.trading_store import TradingStore
from quant_data.trading.broker import BrokerAdapter
from quant_data.trading.ledger import LedgerService


class LiveSyncService:
    """Synchronize broker truth into normalized and generic trading records."""

    def __init__(self, broker: BrokerAdapter, store: TradingStore, *, cache_seconds: float = 2.0) -> None:
        self.broker = broker
        self.store = store
        self.cache_seconds = max(0.0, float(cache_seconds))
        self.ledger = LedgerService(store)
        self.marker_engine = TradingMarkerEngine()
        self._last_sync_monotonic = 0.0
        self._last_result: dict[str, Any] | None = None

    def sync(self, *, session_id: str, force: bool = False) -> dict[str, Any]:
        if not force and self._last_result is not None and time.monotonic() - self._last_sync_monotonic < self.cache_seconds:
            return {**self._last_result, "cache_status": "hit"}
        fetched_at = _now()
        errors: list[str] = []
        health = self._safe_call("health", self.broker.health_check, errors)
        account = self._safe_call("account", self.broker.get_account, errors)
        cash = self._safe_call("cash", self.broker.get_cash, errors)
        positions = self._safe_call("positions", self.broker.get_positions, errors, default=[])
        orders = self._safe_call("orders", self.broker.get_orders, errors, default=[])
        trades = self._safe_call("trades", self.broker.get_trades, errors, default=[])

        health_data = health.to_dict() if hasattr(health, "to_dict") else dict(health or {})
        account_data = account.to_dict() if hasattr(account, "to_dict") else dict(account or {})
        cash_data = cash.to_dict() if hasattr(cash, "to_dict") else dict(cash or {})
        position_rows = [x.to_dict() if hasattr(x, "to_dict") else dict(x or {}) for x in positions or []]
        order_rows = [x.to_dict() if hasattr(x, "to_dict") else dict(x or {}) for x in orders or []]
        trade_rows = [x.to_dict() if hasattr(x, "to_dict") else dict(x or {}) for x in trades or []]
        broker_name = str(health_data.get("broker") or account_data.get("broker") or "disabled")
        account_id = str(account_data.get("account_id") or "")
        authorized = bool(account_data.get("authorized") and health_data.get("connected"))
        source = f"broker:{broker_name}"
        quality_status = "ok" if authorized and not errors else ("unsupported" if health_data.get("status") in {"disabled", "unsupported"} else "missing")

        available_cash = _num(cash_data.get("available_cash"))
        frozen_cash = _num(cash_data.get("frozen_cash"))
        total_cash = _num(cash_data.get("total_cash"), available_cash + frozen_cash)
        position_market_value = sum(_num(row.get("market_value"), _num(row.get("quantity")) * _num(row.get("market_price"))) for row in position_rows)
        total_equity = total_cash + position_market_value
        snapshot_id = _id("account", session_id, account_id, fetched_at)
        account_snapshot = {
            "snapshot_id": snapshot_id,
            "mode": "live",
            "session_id": session_id,
            "broker": broker_name,
            "account_id": account_id,
            "available_cash": available_cash,
            "initial_cash": _num(account_data.get("initial_cash")),
            "cash": total_cash,
            "equity": round(total_equity, 6),
            "market_value": round(position_market_value, 6),
            "frozen_cash": frozen_cash,
            "total_cash": total_cash,
            "position_market_value": round(position_market_value, 6),
            "total_equity": round(total_equity, 6),
            "realized_pnl": _num(account_data.get("realized_pnl")),
            "unrealized_pnl": sum(_position_unrealized(row) for row in position_rows),
            "daily_pnl": _num(account_data.get("daily_pnl")),
            "max_drawdown": _num(account_data.get("max_drawdown")),
            "authorized": int(authorized),
            "fetched_at": fetched_at,
            "available_at": fetched_at,
            "source": source,
            "quality_status": quality_status,
        }
        self.store.put_normalized("broker_accounts", account_snapshot, record_id=snapshot_id)
        self.store.put_normalized(
            "account_equity_curve",
            {
                "point_id": _id("equity", session_id, fetched_at),
                "mode": "live",
                "session_id": session_id,
                "account_id": account_id,
                "equity": total_equity,
                "available_cash": available_cash,
                "position_market_value": position_market_value,
                "realized_pnl": _num(account_data.get("realized_pnl")),
                "unrealized_pnl": sum(_position_unrealized(row) for row in position_rows),
                "return_pct": _num(account_data.get("return_pct")),
                "timestamp": fetched_at,
                "source": source,
            },
        )

        normalized_positions = [self._persist_position(row, snapshot_id, session_id, account_id, broker_name, source, fetched_at) for row in position_rows]
        normalized_orders = [self._persist_order(row, session_id, account_id, broker_name, source, fetched_at) for row in order_rows]
        normalized_trades = [self._persist_trade(row, session_id, account_id, broker_name, source, fetched_at) for row in trade_rows]

        result = {
            "ok": not errors,
            "data_available": authorized,
            "session_id": session_id,
            "broker": health_data,
            "account": {**account_data, **account_snapshot, "authorized": authorized},
            "cash": cash_data,
            "positions": normalized_positions,
            "orders": normalized_orders,
            "trades": normalized_trades,
            "fetched_at": fetched_at,
            "available_at": fetched_at,
            "source": source,
            "quality_status": quality_status,
            "missing_reasons": errors or ([] if authorized else [str(health_data.get("message") or "券商未连接或未授权")]),
            "cache_status": "refreshed",
        }
        self._last_result = result
        self._last_sync_monotonic = time.monotonic()
        return result

    def _safe_call(self, label: str, fn: Any, errors: list[str], default: Any = None) -> Any:
        try:
            return fn()
        except Exception as exc:
            errors.append(f"{label}: {type(exc).__name__}: {exc}")
            return default if default is not None else {}

    def _persist_position(self, row: dict[str, Any], snapshot_id: str, session_id: str, account_id: str, broker: str, source: str, fetched_at: str) -> dict[str, Any]:
        symbol = str(row.get("symbol") or "")
        quantity = _num(row.get("quantity"))
        cost = _num(row.get("avg_cost") or row.get("cost_price"))
        price = _num(row.get("market_price") or row.get("last_price"))
        market_value = _num(row.get("market_value"), quantity * price)
        unrealized = _num(row.get("unrealized_pnl"), market_value - quantity * cost)
        cost_value = quantity * cost
        pnl_pct = _num(row.get("unrealized_pnl_pct"), unrealized / cost_value * 100 if cost_value else 0.0)
        normalized = {
            **row,
            "record_id": _id("position", snapshot_id, symbol),
            "snapshot_id": snapshot_id,
            "session_id": session_id,
            "account_id": account_id,
            "broker": broker,
            "symbol": symbol,
            "quantity": quantity,
            "available_quantity": _num(row.get("available_quantity")),
            "avg_cost": cost,
            "market_price": price,
            "market_value": market_value,
            "unrealized_pnl": unrealized,
            "unrealized_pnl_pct": pnl_pct,
            "fetched_at": fetched_at,
            "source": source,
        }
        self.store.put_normalized("broker_positions", normalized, record_id=normalized["record_id"])
        self.store.put("positions", normalized, mode="live", symbol=symbol, session_id=session_id, record_id=normalized["record_id"])
        return normalized

    def _persist_order(self, row: dict[str, Any], session_id: str, account_id: str, broker: str, source: str, fetched_at: str) -> dict[str, Any]:
        broker_order_id = str(row.get("broker_order_id") or row.get("order_id") or "")
        normalized = {
            **row,
            "record_id": _id("broker-order", broker, broker_order_id),
            "session_id": session_id,
            "account_id": account_id,
            "broker": broker,
            "broker_order_id": broker_order_id,
            "order_id": str(row.get("order_id") or broker_order_id),
            "filled_quantity": _num(row.get("filled_quantity")),
            "updated_at": str(row.get("updated_at") or fetched_at),
            "source": source,
        }
        self.store.put_normalized("broker_orders", normalized, record_id=normalized["record_id"])
        return normalized

    def _persist_trade(self, row: dict[str, Any], session_id: str, account_id: str, broker: str, source: str, fetched_at: str) -> dict[str, Any]:
        broker_trade_id = str(row.get("broker_trade_id") or row.get("trade_id") or "")
        broker_order_id = str(row.get("broker_order_id") or row.get("order_id") or "")
        record_id = _id("broker-trade", broker, broker_trade_id or [broker_order_id, row.get("filled_at"), row.get("quantity"), row.get("price")])
        quantity = _num(row.get("quantity"))
        price = _num(row.get("price"))
        normalized = {
            **row,
            "record_id": record_id,
            "session_id": session_id,
            "account_id": account_id,
            "broker": broker,
            "broker_trade_id": broker_trade_id,
            "broker_order_id": broker_order_id,
            "order_id": str(row.get("order_id") or broker_order_id),
            "quantity": quantity,
            "price": price,
            "amount": _num(row.get("amount"), quantity * price),
            "filled_at": str(row.get("filled_at") or fetched_at),
            "source": source,
        }
        existing = self.store.list_normalized("broker_trades", session_id=session_id, limit=10000)
        is_new = not any(str(item.get("record_id") or "") == record_id for item in existing)
        self.store.put_normalized("broker_trades", normalized, record_id=record_id)
        if is_new:
            fill = {
                **normalized,
                "fill_id": broker_trade_id or record_id,
                "mode": "live",
                "source": source,
            }
            self.store.put("fills", fill, mode="live", symbol=str(fill.get("symbol") or ""), session_id=session_id, record_id=str(fill["fill_id"]))
            self.ledger.record_fill(fill, mode="live", session_id=session_id, account_id=account_id, source=source)
            marker = self.marker_engine.from_fill(fill, mode="live", session_id=session_id).to_dict()
            self.store.put("chart_markers", marker, mode="live", symbol=str(fill.get("symbol") or ""), session_id=session_id, record_id=marker["marker_id"])
        return normalized


def _position_unrealized(row: dict[str, Any]) -> float:
    quantity = _num(row.get("quantity"))
    cost = _num(row.get("avg_cost") or row.get("cost_price"))
    price = _num(row.get("market_price") or row.get("last_price"))
    return _num(row.get("unrealized_pnl"), quantity * (price - cost))


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except Exception:
        return default


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _id(*parts: Any) -> str:
    raw = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return sha256(raw.encode("utf-8")).hexdigest()[:24]
