from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .base import BrokerAdapter
from .broker_config import BrokerConfig, load_broker_config
from .broker_models import (
    BrokerAccountSnapshot,
    BrokerCash,
    BrokerConnectionStatus,
    BrokerOrder,
    BrokerPosition,
    BrokerTrade,
    CancelOrderResult,
    LiveOrderAck,
    LiveOrderRequest,
)


BridgeTransport = Callable[[str, str, dict[str, Any] | None], dict[str, Any]]


class HttpBridgeBrokerAdapter(BrokerAdapter):
    """Connect an explicitly authorized local broker bridge to the live core.

    The adapter does not expose an Internet broker API. Remote hosts are
    rejected unless BROKER_HTTP_ALLOW_REMOTE=true, and a token is always
    required. Every unsuccessful or malformed response remains unsuccessful.
    """

    def __init__(self, config: BrokerConfig | None = None, *, transport: BridgeTransport | None = None) -> None:
        self.config = config or load_broker_config()
        self.transport = transport
        self.last_error = ""

    def connect(self) -> BrokerConnectionStatus:
        ready = self._configuration_status()
        if ready is not None:
            return ready
        try:
            self._request("POST", "/connect", {})
        except Exception as exc:
            self.last_error = str(exc)[:240]
            return self._status(False, "disconnected", self.last_error)
        return self.health_check()

    def disconnect(self) -> None:
        try:
            self._request("POST", "/disconnect", {})
        except Exception as exc:
            self.last_error = str(exc)[:240]

    def health_check(self) -> BrokerConnectionStatus:
        ready = self._configuration_status()
        if ready is not None:
            return ready
        try:
            payload = self._unwrap(self._request("GET", "/health"))
        except Exception as exc:
            self.last_error = str(exc)[:240]
            return self._status(False, "disconnected", self.last_error)
        connected = payload.get("connected") is True
        status = str(payload.get("status") or ("connected" if connected else "disconnected"))
        message = str(payload.get("message") or ("本地券商桥已连接" if connected else "本地券商桥未连接"))
        return self._status(connected, status, message, raw=payload)

    def get_account(self) -> BrokerAccountSnapshot:
        payload = self._unwrap(self._request("GET", "/account"))
        cash = self._cash(payload.get("cash") if isinstance(payload.get("cash"), dict) else payload)
        positions = [self._position(row) for row in payload.get("positions", []) if isinstance(row, dict)]
        return BrokerAccountSnapshot(
            account_id=str(payload.get("account_id") or ""),
            broker="http_bridge",
            cash=cash,
            positions=positions,
            fetched_at=str(payload.get("fetched_at") or datetime.now().isoformat(timespec="seconds")),
            authorized=payload.get("authorized") is True,
            source=str(payload.get("source") or "authorized_local_http_bridge"),
            available_at=str(payload.get("available_at") or payload.get("fetched_at") or ""),
            quality_status=str(payload.get("quality_status") or "ok"),
        )

    def get_positions(self) -> list[BrokerPosition]:
        payload = self._unwrap(self._request("GET", "/positions"))
        rows = payload.get("items") if isinstance(payload, dict) else []
        if not isinstance(rows, list):
            rows = payload.get("positions", []) if isinstance(payload, dict) else []
        return [self._position(row) for row in rows if isinstance(row, dict)]

    def get_cash(self) -> BrokerCash:
        return self._cash(self._unwrap(self._request("GET", "/cash")))

    def get_orders(self) -> list[BrokerOrder]:
        payload = self._unwrap(self._request("GET", "/orders"))
        return [self._order(row) for row in self._rows(payload, "orders")]

    def get_trades(self, order_id: str | None = None) -> list[BrokerTrade]:
        path = "/trades" + (f"?order_id={order_id}" if order_id else "")
        payload = self._unwrap(self._request("GET", path))
        return [self._trade(row) for row in self._rows(payload, "trades")]

    def place_order(self, request: LiveOrderRequest) -> LiveOrderAck:
        if not self.config.feature_live_broker or not self.config.live_trading_enabled:
            return LiveOrderAck(False, "rejected", reason="真实交易功能未显式开启，本地券商桥拒绝下单")
        if self.config.live_kill_switch:
            return LiveOrderAck(False, "rejected", reason="LIVE_KILL_SWITCH=true，本地券商桥拒绝下单")
        try:
            payload = self._unwrap(self._request("POST", "/orders", request.to_dict()))
        except Exception as exc:
            return LiveOrderAck(False, "failed", reason=str(exc)[:240])
        accepted = payload.get("accepted") is True
        return LiveOrderAck(
            accepted=accepted,
            status=_order_status(payload.get("status"), fallback="accepted" if accepted else "rejected"),
            order_id=str(payload.get("order_id") or ""),
            broker_order_id=str(payload.get("broker_order_id") or payload.get("order_id") or ""),
            reason=str(payload.get("reason") or payload.get("message") or ""),
            raw_response=payload,
        )

    def cancel_order(self, order_id: str) -> CancelOrderResult:
        try:
            payload = self._unwrap(self._request("POST", f"/orders/{order_id}/cancel", {}))
        except Exception as exc:
            return CancelOrderResult(False, order_id, "failed", str(exc)[:240])
        return CancelOrderResult(
            ok=payload.get("ok") is True,
            order_id=str(payload.get("order_id") or order_id),
            status=_order_status(payload.get("status"), fallback="cancel_requested" if payload.get("ok") is True else "unknown"),
            reason=str(payload.get("reason") or payload.get("message") or ""),
        )

    def query_order(self, order_id: str) -> BrokerOrder:
        try:
            payload = self._unwrap(self._request("GET", f"/orders/{order_id}"))
            return self._order(payload)
        except Exception as exc:
            return BrokerOrder(order_id=order_id, symbol="", side="", status="unknown", raw_response={"error": str(exc)[:240]})

    def _configuration_status(self) -> BrokerConnectionStatus | None:
        if not self.config.http_bridge_url or not self.config.http_bridge_token:
            return self._status(False, "unsupported", "缺少 BROKER_HTTP_URL 或 BROKER_HTTP_TOKEN")
        parsed = urlparse(self.config.http_bridge_url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in {"http", "https"} or not host:
            return self._status(False, "unsupported", "BROKER_HTTP_URL 不是有效的 HTTP(S) 地址")
        if not self.config.http_bridge_allow_remote and host not in {"127.0.0.1", "localhost", "::1"}:
            return self._status(False, "blocked", "默认只允许本机券商桥；远程地址已被安全策略阻断")
        return None

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.transport is not None:
            result = self.transport(method, path, payload)
            if not isinstance(result, dict):
                raise ValueError("券商桥返回值不是 JSON 对象")
            return result
        ready = self._configuration_status()
        if ready is not None:
            raise RuntimeError(ready.message)
        url = self.config.http_bridge_url.rstrip("/") + path
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        request = Request(
            url,
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.config.http_bridge_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self.config.http_bridge_timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            raise RuntimeError(f"券商桥 HTTP {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError(f"券商桥连接失败: {exc.reason}") from exc
        try:
            result = json.loads(raw or "{}")
        except json.JSONDecodeError as exc:
            raise RuntimeError("券商桥返回非 JSON 数据") from exc
        if not isinstance(result, dict):
            raise RuntimeError("券商桥返回值不是 JSON 对象")
        return result

    def _status(self, connected: bool, status: str, message: str, *, raw: dict[str, Any] | None = None) -> BrokerConnectionStatus:
        return BrokerConnectionStatus(
            connected=connected,
            status=status,
            broker="http_bridge",
            message=message,
            live_trading_enabled=self.config.live_trading_enabled,
            order_confirm_required=self.config.order_confirm_required,
            raw=dict(raw or {}),
        )

    @staticmethod
    def _unwrap(payload: dict[str, Any]) -> dict[str, Any]:
        data = payload.get("data") if isinstance(payload, dict) else None
        return dict(data) if isinstance(data, dict) else dict(payload or {})

    @staticmethod
    def _rows(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
        rows = payload.get("items") or payload.get(key) or []
        return [dict(row) for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []

    @staticmethod
    def _cash(row: dict[str, Any]) -> BrokerCash:
        return BrokerCash(
            available_cash=float(row.get("available_cash") or row.get("cash") or 0),
            frozen_cash=float(row.get("frozen_cash") or 0),
            total_cash=float(row.get("total_cash") or row.get("cash") or row.get("available_cash") or 0),
            currency=str(row.get("currency") or "CNY"),
        )

    @staticmethod
    def _position(row: dict[str, Any]) -> BrokerPosition:
        return BrokerPosition(
            symbol=str(row.get("symbol") or row.get("code") or ""),
            name=str(row.get("name") or ""),
            quantity=int(float(row.get("quantity") or row.get("qty") or 0)),
            available_quantity=int(float(row.get("available_quantity") or row.get("available") or 0)),
            avg_cost=float(row.get("avg_cost") or row.get("cost_price") or 0),
            market_price=float(row.get("market_price") or row.get("last_price") or 0),
            market_value=float(row.get("market_value") or 0),
            unrealized_pnl=float(row.get("unrealized_pnl") or 0),
            unrealized_pnl_pct=float(row.get("unrealized_pnl_pct") or 0),
            source=str(row.get("source") or "authorized_local_http_bridge"),
            fetched_at=str(row.get("fetched_at") or datetime.now().isoformat(timespec="seconds")),
            available_at=str(row.get("available_at") or row.get("fetched_at") or ""),
            quality_status=str(row.get("quality_status") or "ok"),
        )

    @staticmethod
    def _order(row: dict[str, Any]) -> BrokerOrder:
        return BrokerOrder(
            order_id=str(row.get("order_id") or row.get("broker_order_id") or ""),
            broker_order_id=str(row.get("broker_order_id") or row.get("order_id") or ""),
            symbol=str(row.get("symbol") or ""),
            side=_side(row.get("side")),
            status=_order_status(row.get("status")),
            quantity=int(float(row.get("quantity") or 0)),
            filled_quantity=int(float(row.get("filled_quantity") or 0)),
            price=float(row["price"]) if row.get("price") not in (None, "") else None,
            created_at=str(row.get("created_at") or datetime.now().isoformat(timespec="seconds")),
            updated_at=str(row.get("updated_at") or datetime.now().isoformat(timespec="seconds")),
            source=str(row.get("source") or "authorized_local_http_bridge"),
            raw_response=row,
        )

    @staticmethod
    def _trade(row: dict[str, Any]) -> BrokerTrade:
        quantity = int(float(row.get("quantity") or 0))
        price = float(row.get("price") or 0)
        return BrokerTrade(
            trade_id=str(row.get("trade_id") or row.get("broker_trade_id") or ""),
            order_id=str(row.get("order_id") or ""),
            broker_order_id=str(row.get("broker_order_id") or row.get("order_id") or ""),
            symbol=str(row.get("symbol") or ""),
            side=_side(row.get("side")),
            quantity=quantity,
            price=price,
            amount=float(row.get("amount") or quantity * price),
            fee=float(row.get("fee") or 0),
            tax=float(row.get("tax") or 0),
            slippage=float(row.get("slippage") or 0),
            filled_at=str(row.get("filled_at") or datetime.now().isoformat(timespec="seconds")),
            source=str(row.get("source") or "authorized_local_http_bridge"),
            raw_response=row,
        )


def _side(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"buy", "b", "23", "stock_buy", "买入", "证券买入"} or "买入" in text:
        return "buy"
    if text in {"sell", "s", "24", "stock_sell", "卖出", "证券卖出"} or "卖出" in text:
        return "sell"
    return ""


def _order_status(value: Any, *, fallback: str = "unknown") -> str:
    text = str(value if value is not None else "").strip().lower().replace(" ", "")
    aliases = {
        "signal_created": "signal_created",
        "prechecked": "prechecked",
        "risk_blocked": "risk_blocked",
        "needs_confirmation": "needs_confirmation",
        "confirmed": "confirmed",
        "submitted": "submitted",
        "pending": "submitted",
        "待报": "submitted",
        "accepted": "accepted",
        "已报": "accepted",
        "partially_filled": "partially_filled",
        "partial": "partially_filled",
        "部成": "partially_filled",
        "filled": "filled",
        "done": "filled",
        "已成": "filled",
        "cancel_requested": "cancel_requested",
        "待撤": "cancel_requested",
        "cancelled": "cancelled",
        "canceled": "cancelled",
        "已撤": "cancelled",
        "rejected": "rejected",
        "废单": "rejected",
        "failed": "failed",
        "expired": "expired",
        "unknown": "unknown",
        "reconciled": "reconciled",
    }
    return aliases.get(text, fallback)
