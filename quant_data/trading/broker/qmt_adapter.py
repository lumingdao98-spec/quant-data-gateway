from __future__ import annotations

from datetime import datetime
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


class QmtBrokerAdapter(DisabledBrokerAdapter):
    def __init__(self, config: BrokerConfig | None = None) -> None:
        super().__init__(config or load_broker_config())
        self._supported = self._check_sdk()
        self._trader: Any = None
        self._account: Any = None
        self._connected = False
        self._last_error = ""

    def _check_sdk(self) -> bool:
        try:
            importlib.import_module("xtquant.xttrader")
            importlib.import_module("xtquant.xttype")
            importlib.import_module("xtquant.xtconstant")
            return True
        except Exception:
            return False

    def health_check(self) -> BrokerConnectionStatus:
        if not self._supported:
            return BrokerConnectionStatus(False, "unsupported", "qmt", "本机未安装或无法导入 xtquant，QMT 适配器不可用。")
        if not (self.config.feature_live_broker and self.config.live_trading_enabled):
            return BrokerConnectionStatus(False, "disabled", "qmt", "QMT SDK 已识别，但真实交易开关未开启。")
        missing = [name for name, value in (("QMT_PATH", self.config.qmt_path), ("QMT_ACCOUNT_ID", self.config.qmt_account_id), ("QMT_SESSION_ID", self.config.qmt_session_id)) if not value]
        if missing:
            return BrokerConnectionStatus(False, "unauthorized", "qmt", "缺少配置：" + ", ".join(missing))
        if not self._connected:
            return BrokerConnectionStatus(False, "not_connected", "qmt", self._last_error or "QMT 已配置但尚未连接。")
        return BrokerConnectionStatus(True, "connected", "qmt", "QMT 已连接。", True, self.config.order_confirm_required)

    def connect(self) -> BrokerConnectionStatus:
        status = self.health_check()
        if status.status in {"unsupported", "disabled", "unauthorized"}:
            return status
        try:
            xttrader = importlib.import_module("xtquant.xttrader")
            xttype = importlib.import_module("xtquant.xttype")
            self._trader = xttrader.XtQuantTrader(self.config.qmt_path, int(self.config.qmt_session_id))
            self._trader.start()
            connect_result = self._trader.connect()
            if connect_result not in (0, None):
                raise RuntimeError(f"QMT connect returned {connect_result}")
            self._account = xttype.StockAccount(self.config.qmt_account_id, self.config.qmt_account_type or "STOCK")
            subscribe_result = self._trader.subscribe(self._account)
            if subscribe_result not in (0, None):
                raise RuntimeError(f"QMT subscribe returned {subscribe_result}")
            self._connected = True
            self._last_error = ""
        except Exception as exc:
            self._connected = False
            self._last_error = f"{type(exc).__name__}: {exc}"
        return self.health_check()

    def disconnect(self) -> None:
        try:
            if self._trader is not None and hasattr(self._trader, "stop"):
                self._trader.stop()
        finally:
            self._connected = False

    def get_cash(self) -> BrokerCash:
        asset = self._query("query_stock_asset")
        available = _num(_attr(asset, "cash", "available_cash"))
        frozen = _num(_attr(asset, "frozen_cash"))
        return BrokerCash(available_cash=available, frozen_cash=frozen, total_cash=available + frozen)

    def get_account(self) -> BrokerAccountSnapshot:
        return BrokerAccountSnapshot(
            account_id=self.config.qmt_account_id,
            broker="qmt",
            cash=self.get_cash(),
            positions=self.get_positions(),
            authorized=self._connected,
            source="broker:qmt",
            quality_status="ok" if self._connected else "missing",
        )

    def get_positions(self) -> list[BrokerPosition]:
        rows = self._query("query_stock_positions", default=[])
        out: list[BrokerPosition] = []
        for row in rows or []:
            quantity = int(_num(_attr(row, "volume", "quantity")))
            cost = _num(_attr(row, "open_price", "avg_price", "avg_cost"))
            market_value = _num(_attr(row, "market_value"))
            price = _num(_attr(row, "last_price", "market_price"), market_value / quantity if quantity else 0.0)
            unrealized = market_value - quantity * cost
            out.append(BrokerPosition(
                symbol=_symbol(_attr(row, "stock_code", "symbol")),
                name=str(_attr(row, "stock_name", "name") or ""),
                quantity=quantity,
                available_quantity=int(_num(_attr(row, "can_use_volume", "available_quantity"))),
                avg_cost=cost,
                market_price=price,
                market_value=market_value,
                unrealized_pnl=unrealized,
                unrealized_pnl_pct=unrealized / (quantity * cost) * 100 if quantity and cost else 0.0,
                source="broker:qmt",
            ))
        return out

    def get_orders(self) -> list[BrokerOrder]:
        return [self._map_order(row) for row in self._query("query_stock_orders", default=[]) or []]

    def get_trades(self, order_id: str | None = None) -> list[BrokerTrade]:
        rows = [self._map_trade(row) for row in self._query("query_stock_trades", default=[]) or []]
        return [row for row in rows if not order_id or row.order_id == order_id or row.broker_order_id == order_id]

    def place_order(self, request: LiveOrderRequest) -> LiveOrderAck:
        if not self._connected or not (self.config.feature_live_broker and self.config.live_trading_enabled):
            return LiveOrderAck(False, "rejected", reason="QMT 未连接或真实交易开关未开启。", raw_response={"request": request.to_dict()})
        try:
            constant = importlib.import_module("xtquant.xtconstant")
            side = constant.STOCK_BUY if request.side.lower() == "buy" else constant.STOCK_SELL
            price_type = getattr(constant, "FIX_PRICE", 11)
            broker_order_id = self._trader.order_stock(
                self._account, _market_symbol(request.symbol), side, int(request.quantity), price_type,
                float(request.limit_price or 0.0), str(request.strategy_family or "v324"), str(request.signal_id or ""),
            )
            accepted = str(broker_order_id or "") not in {"", "-1"}
            return LiveOrderAck(accepted, "submitted" if accepted else "rejected", order_id=str(broker_order_id or ""), broker_order_id=str(broker_order_id or ""), reason="QMT 已接收委托" if accepted else "QMT 拒绝委托")
        except Exception as exc:
            return LiveOrderAck(False, "failed", reason=f"{type(exc).__name__}: {exc}", raw_response={"request": request.to_dict()})

    def cancel_order(self, order_id: str) -> CancelOrderResult:
        if not self._connected:
            return CancelOrderResult(False, order_id, "unsupported", "QMT 未连接")
        try:
            result = self._trader.cancel_order_stock(self._account, int(order_id))
            ok = result in (0, None)
            return CancelOrderResult(ok, order_id, "cancel_requested" if ok else "failed", "" if ok else f"QMT cancel returned {result}")
        except Exception as exc:
            return CancelOrderResult(False, order_id, "failed", f"{type(exc).__name__}: {exc}")

    def query_order(self, order_id: str) -> BrokerOrder:
        match = next((row for row in self.get_orders() if row.order_id == order_id or row.broker_order_id == order_id), None)
        return match or BrokerOrder(order_id=order_id, symbol="", side="", status="unknown", source="broker:qmt")

    def _query(self, method: str, default: Any = None) -> Any:
        if not self._connected or self._trader is None or self._account is None:
            return default if default is not None else None
        return getattr(self._trader, method)(self._account)

    def _map_order(self, row: Any) -> BrokerOrder:
        order_id = str(_attr(row, "order_id") or "")
        return BrokerOrder(
            order_id=order_id, broker_order_id=order_id,
            symbol=_symbol(_attr(row, "stock_code", "symbol")), side=_side(_attr(row, "order_type", "side")),
            status=str(_attr(row, "order_status", "status") or "unknown"),
            quantity=int(_num(_attr(row, "order_volume", "quantity"))), price=_num(_attr(row, "price", "order_price")),
            filled_quantity=int(_num(_attr(row, "traded_volume", "filled_quantity"))),
            created_at=_time_text(_attr(row, "order_time", "created_at")), source="broker:qmt", raw_response=_raw(row),
        )

    def _map_trade(self, row: Any) -> BrokerTrade:
        quantity = int(_num(_attr(row, "traded_volume", "quantity")))
        price = _num(_attr(row, "traded_price", "price"))
        order_id = str(_attr(row, "order_id") or "")
        return BrokerTrade(
            trade_id=str(_attr(row, "traded_id", "trade_id") or ""), order_id=order_id, broker_order_id=order_id,
            symbol=_symbol(_attr(row, "stock_code", "symbol")), side=_side(_attr(row, "order_type", "side")),
            quantity=quantity, price=price, amount=_num(_attr(row, "traded_amount", "amount"), quantity * price),
            filled_at=_time_text(_attr(row, "traded_time", "filled_at")), source="broker:qmt", raw_response=_raw(row),
        )


def _attr(value: Any, *names: str) -> Any:
    for name in names:
        if isinstance(value, dict) and name in value:
            return value[name]
        if hasattr(value, name):
            return getattr(value, name)
    return None


def _raw(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else dict(getattr(value, "__dict__", {}) or {})


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except Exception:
        return default


def _symbol(value: Any) -> str:
    return str(value or "").split(".", 1)[0].zfill(6)[-6:]


def _market_symbol(symbol: str) -> str:
    code = _symbol(symbol)
    return f"{code}.SH" if code.startswith(("5", "6", "9")) else f"{code}.SZ"


def _side(value: Any) -> str:
    text = str(value or "").lower()
    return "buy" if text in {"23", "buy", "stock_buy"} or "buy" in text else "sell" if text else ""


def _time_text(value: Any) -> str:
    if isinstance(value, (int, float)) and value > 1_000_000_000:
        return datetime.fromtimestamp(value).isoformat(timespec="seconds")
    return str(value or datetime.now().isoformat(timespec="seconds"))
