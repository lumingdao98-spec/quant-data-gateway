from __future__ import annotations

import importlib
from typing import Any

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
from .disabled import DisabledBrokerAdapter


class PTradeBrokerAdapter(DisabledBrokerAdapter):
    """Guarded PTrade adapter for user-authorized local SDK environments.

    PTrade distributions do not expose one universal Python API. The adapter
    accepts a configurable module/factory and refuses to claim support when the
    required methods are absent.
    """

    def __init__(self, config: BrokerConfig | None = None) -> None:
        super().__init__(config or load_broker_config())
        self._module: Any = None
        self._client: Any = None
        self._connected = False
        self._last_error = ""
        self._supported = self._check_sdk()

    def _check_sdk(self) -> bool:
        try:
            self._module = importlib.import_module(self.config.ptrade_module or "ptrade")
            return True
        except Exception:
            return False

    def health_check(self) -> BrokerConnectionStatus:
        if not self._supported:
            return BrokerConnectionStatus(
                False,
                "unsupported",
                "ptrade",
                "PTrade 通常运行在券商托管平台；当前未识别券商明确提供的本地模块。"
                "可在券商环境部署受控执行端后使用本地 HTTP 券商桥，或配置券商给出的模块/工厂。",
            )
        if not (self.config.feature_live_broker and self.config.live_trading_enabled):
            return BrokerConnectionStatus(False, "disabled", "ptrade", "PTrade SDK 已识别，但真实交易开关未开启。")
        if not self.config.ptrade_account_id:
            return BrokerConnectionStatus(False, "unauthorized", "ptrade", "PTRADE_ACCOUNT_ID 未配置。")
        if not self._connected:
            return BrokerConnectionStatus(False, "not_connected", "ptrade", self._last_error or "PTrade 已配置但尚未连接。")
        return BrokerConnectionStatus(True, "connected", "ptrade", "PTrade 已连接。", True, self.config.order_confirm_required)

    def connect(self) -> BrokerConnectionStatus:
        status = self.health_check()
        if status.status in {"unsupported", "disabled", "unauthorized"}:
            return status
        try:
            factory_name = self.config.ptrade_client_factory
            if factory_name:
                factory = getattr(self._module, factory_name)
                self._client = factory(path=self.config.ptrade_path, account_id=self.config.ptrade_account_id)
            elif hasattr(self._module, "create_client"):
                self._client = self._module.create_client(path=self.config.ptrade_path, account_id=self.config.ptrade_account_id)
            elif hasattr(self._module, "Client"):
                self._client = self._module.Client(path=self.config.ptrade_path, account_id=self.config.ptrade_account_id)
            else:
                raise RuntimeError("PTrade SDK 未暴露可配置的 Client/create_client 工厂")
            if hasattr(self._client, "connect"):
                result = self._client.connect()
                if result not in (True, 0, None):
                    raise RuntimeError(f"PTrade connect returned {result}")
            required_methods = {
                "get_cash",
                "get_positions",
                "get_orders",
                "get_trades",
                "place_order",
                "cancel_order",
            }
            missing_methods = sorted(name for name in required_methods if not callable(getattr(self._client, name, None)))
            if missing_methods:
                raise RuntimeError("PTrade 执行端缺少必要接口: " + ", ".join(missing_methods))
            self._connected = True
            self._last_error = ""
        except Exception as exc:
            self._connected = False
            self._last_error = f"{type(exc).__name__}: {exc}"
        return self.health_check()

    def disconnect(self) -> None:
        try:
            if self._client is not None and hasattr(self._client, "disconnect"):
                self._client.disconnect()
        finally:
            self._connected = False

    def get_cash(self) -> BrokerCash:
        data = self._call("get_cash", default={})
        return BrokerCash(
            available_cash=_num(_value(data, "available_cash", "cash", "enable_balance")),
            frozen_cash=_num(_value(data, "frozen_cash", "frozen_balance")),
            total_cash=_num(_value(data, "total_cash", "asset_balance", "total_asset")),
        )

    def get_account(self) -> BrokerAccountSnapshot:
        raw = self._call("get_account", default={})
        cash = self.get_cash()
        return BrokerAccountSnapshot(
            account_id=str(_value(raw, "account_id") or self.config.ptrade_account_id),
            broker="ptrade",
            cash=cash,
            positions=self.get_positions(),
            authorized=self._connected,
            source="broker:ptrade",
            quality_status="ok" if self._connected else "missing",
        )

    def get_positions(self) -> list[BrokerPosition]:
        rows = self._call("get_positions", default=[])
        out: list[BrokerPosition] = []
        for row in rows or []:
            quantity = int(_num(_value(row, "quantity", "current_amount", "total_amount")))
            cost = _num(_value(row, "avg_cost", "cost_price", "cost_basis"))
            price = _num(_value(row, "market_price", "last_price"))
            market_value = _num(_value(row, "market_value"), quantity * price)
            unrealized = _num(_value(row, "unrealized_pnl"), market_value - quantity * cost)
            out.append(BrokerPosition(
                symbol=_symbol(_value(row, "symbol", "stock_code", "security")),
                name=str(_value(row, "name", "stock_name") or ""),
                quantity=quantity,
                available_quantity=int(_num(_value(row, "available_quantity", "enable_amount"))),
                avg_cost=cost,
                market_price=price,
                market_value=market_value,
                unrealized_pnl=unrealized,
                unrealized_pnl_pct=unrealized / (quantity * cost) * 100 if quantity and cost else 0.0,
                source="broker:ptrade",
            ))
        return out

    def get_orders(self) -> list[BrokerOrder]:
        rows = self._call("get_orders", default=[])
        return [self._map_order(row) for row in rows or []]

    def get_trades(self, order_id: str | None = None) -> list[BrokerTrade]:
        rows = self._call("get_trades", order_id=order_id, default=[])
        out = [self._map_trade(row) for row in rows or []]
        return [row for row in out if not order_id or row.order_id == order_id or row.broker_order_id == order_id]

    def place_order(self, request: LiveOrderRequest) -> LiveOrderAck:
        if not self._connected or not (self.config.feature_live_broker and self.config.live_trading_enabled):
            return LiveOrderAck(False, "rejected", reason="PTrade 未连接或真实交易开关未开启。", raw_response={"request": request.to_dict()})
        try:
            raw = self._call(
                "place_order",
                symbol=request.symbol,
                side=request.side,
                quantity=int(request.quantity),
                order_type=request.order_type,
                limit_price=request.limit_price,
            )
            order_id = str(_value(raw, "broker_order_id", "order_id") or raw or "")
            accepted = bool(order_id and order_id not in {"-1", "False"})
            return LiveOrderAck(accepted, "submitted" if accepted else "rejected", order_id=order_id, broker_order_id=order_id, reason="PTrade 已接收委托" if accepted else "PTrade 拒绝委托", raw_response=_dict(raw))
        except Exception as exc:
            return LiveOrderAck(False, "failed", reason=f"{type(exc).__name__}: {exc}", raw_response={"request": request.to_dict()})

    def cancel_order(self, order_id: str) -> CancelOrderResult:
        if not self._connected:
            return CancelOrderResult(False, order_id, "unsupported", "PTrade 未连接")
        try:
            raw = self._call("cancel_order", order_id=order_id)
            ok = raw in (True, 0, None) or bool(_value(raw, "ok", "success"))
            return CancelOrderResult(ok, order_id, "cancel_requested" if ok else "failed", "" if ok else str(raw))
        except Exception as exc:
            return CancelOrderResult(False, order_id, "failed", f"{type(exc).__name__}: {exc}")

    def query_order(self, order_id: str) -> BrokerOrder:
        if self._client is not None and hasattr(self._client, "query_order"):
            return self._map_order(self._call("query_order", order_id=order_id))
        match = next((row for row in self.get_orders() if row.order_id == order_id or row.broker_order_id == order_id), None)
        return match or BrokerOrder(order_id=order_id, symbol="", side="", status="unknown", source="broker:ptrade")

    def _call(self, method: str, default: Any = None, **kwargs: Any) -> Any:
        if not self._connected or self._client is None:
            return default
        fn = getattr(self._client, method, None)
        if not callable(fn):
            if default is not None:
                return default
            raise RuntimeError(f"PTrade client does not support {method}")
        return fn(**kwargs)

    def _map_order(self, row: Any) -> BrokerOrder:
        order_id = str(_value(row, "broker_order_id", "order_id", "entrust_no") or "")
        return BrokerOrder(
            order_id=order_id, broker_order_id=order_id,
            symbol=_symbol(_value(row, "symbol", "stock_code")), side=_side(_value(row, "side", "business_name")),
            status=_order_status(_value(row, "status", "order_status", "entrust_status")),
            quantity=int(_num(_value(row, "quantity", "entrust_amount"))), price=_num(_value(row, "price", "entrust_price")),
            filled_quantity=int(_num(_value(row, "filled_quantity", "business_amount"))),
            created_at=str(_value(row, "created_at", "entrust_time") or ""), source="broker:ptrade", raw_response=_dict(row),
        )

    def _map_trade(self, row: Any) -> BrokerTrade:
        quantity = int(_num(_value(row, "quantity", "business_amount")))
        price = _num(_value(row, "price", "business_price"))
        order_id = str(_value(row, "broker_order_id", "order_id", "entrust_no") or "")
        return BrokerTrade(
            trade_id=str(_value(row, "broker_trade_id", "trade_id", "business_no") or ""), order_id=order_id, broker_order_id=order_id,
            symbol=_symbol(_value(row, "symbol", "stock_code")), side=_side(_value(row, "side", "business_name")),
            quantity=quantity, price=price, amount=_num(_value(row, "amount", "business_balance"), quantity * price),
            filled_at=str(_value(row, "filled_at", "business_time") or ""), fee=_num(_value(row, "fee", "fare0")),
            tax=_num(_value(row, "tax", "fare1")), source="broker:ptrade", raw_response=_dict(row),
        )


def _value(value: Any, *names: str) -> Any:
    for name in names:
        if isinstance(value, dict) and name in value:
            return value[name]
        if hasattr(value, name):
            return getattr(value, name)
    return None


def _dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return dict(getattr(value, "__dict__", {}) or {})


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except Exception:
        return default


def _symbol(value: Any) -> str:
    return str(value or "").split(".", 1)[0].zfill(6)[-6:]


def _side(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"buy", "b", "23", "stock_buy", "买入", "证券买入"} or "买入" in text:
        return "buy"
    if text in {"sell", "s", "24", "stock_sell", "卖出", "证券卖出"} or "卖出" in text:
        return "sell"
    return ""


def _order_status(value: Any) -> str:
    text = str(value if value is not None else "").strip().lower().replace(" ", "")
    if text in {"submitted", "pending", "待报", "未报"}:
        return "submitted"
    if text in {"accepted", "reported", "已报", "已受理", "已确认"}:
        return "accepted"
    if text in {"cancel_requested", "撤单中", "待撤", "已报待撤", "部成待撤"}:
        return "cancel_requested"
    if text in {"partially_filled", "partial", "部成", "部分成交"}:
        return "partially_filled"
    if text in {"filled", "done", "已成", "全部成交", "成交"}:
        return "filled"
    if text in {"cancelled", "canceled", "已撤", "部撤", "撤单"}:
        return "cancelled"
    if text in {"rejected", "废单", "拒单", "已拒绝"}:
        return "rejected"
    if text in {"failed", "失败"}:
        return "failed"
    if text in {"expired", "已过期"}:
        return "expired"
    return "unknown"
