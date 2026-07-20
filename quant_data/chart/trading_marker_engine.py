from __future__ import annotations

from hashlib import sha256
from typing import Any

from .marker_models import ChartMarker


class TradingMarkerEngine:
    """Translate the unified order lifecycle into compact chart markers."""

    def from_order(self, order: dict[str, Any]) -> ChartMarker:
        status = _canonical_status(order.get("status"))
        side = str(order.get("side") or "").lower()
        marker_type = _order_marker_type(status, side)
        timestamp = str(
            order.get("filled_at")
            or order.get("cancelled_at")
            or order.get("updated_at")
            or order.get("submitted_at")
            or order.get("created_at")
            or ""
        )
        return ChartMarker(
            marker_id=_id(order.get("order_id"), marker_type, timestamp),
            symbol=str(order.get("symbol") or ""),
            mode=str(order.get("mode") or "paper"),
            session_id=str(order.get("session_id") or ""),
            timestamp=timestamp,
            price=_float(order.get("limit_price") or order.get("price")),
            marker_type=marker_type,
            side=side,
            quantity=_int(order.get("quantity")),
            label=_label(marker_type),
            tooltip=_order_tooltip(order, status),
            source_ref=str(order.get("source_ref") or order.get("broker_order_id") or ""),
            order_id=str(order.get("order_id") or ""),
            signal_id=str(order.get("signal_id") or ""),
            provenance_id=str(order.get("provenance_id") or ""),
            confidence=0.9 if status in {"accepted", "partially_filled", "filled"} else 0.6,
            explanation=str(order.get("status_reason") or order.get("reason") or _status_cn(status)),
        )

    def from_fill(
        self,
        fill: dict[str, Any],
        *,
        mode: str = "paper",
        session_id: str = "",
    ) -> ChartMarker:
        side = str(fill.get("side") or "").lower()
        partial = bool(fill.get("partial")) or str(fill.get("status") or "") == "partially_filled"
        marker_type = "partial_fill" if partial else f"{side}_fill" if side else "fill"
        quantity = _int(fill.get("quantity"))
        price = _float(fill.get("price"))
        return ChartMarker(
            marker_id=_id(fill.get("fill_id"), marker_type, fill.get("filled_at")),
            symbol=str(fill.get("symbol") or ""),
            mode=mode,
            session_id=session_id or str(fill.get("session_id") or ""),
            timestamp=str(fill.get("filled_at") or fill.get("date") or ""),
            price=price,
            marker_type=marker_type,
            side=side,
            quantity=quantity,
            label=_label(marker_type),
            tooltip=f"{_side_cn(side)}成交 {quantity} 股，价格 {price:g}",
            source_ref=str(fill.get("source") or fill.get("broker_trade_id") or ""),
            order_id=str(fill.get("order_id") or ""),
            fill_id=str(fill.get("fill_id") or ""),
            provenance_id=str(fill.get("provenance_id") or ""),
            confidence=0.98,
            explanation="成交回报已写入统一账本",
        )

    def behavior_marker(
        self,
        symbol: str,
        item: dict[str, Any],
        *,
        mode: str = "analysis",
    ) -> ChartMarker:
        return ChartMarker(
            marker_id=_id(symbol, item.get("timestamp"), item.get("label")),
            symbol=symbol,
            mode=mode,
            session_id=str(item.get("session_id") or ""),
            timestamp=str(item.get("timestamp") or item.get("date") or ""),
            price=_float(item.get("price")),
            marker_type=str(item.get("marker_type") or "behavior_risk"),
            label=str(item.get("label") or "异常"),
            tooltip=str(item.get("tooltip") or item.get("explanation") or ""),
            source_ref=str(item.get("source_ref") or item.get("source") or ""),
            confidence=_float(item.get("confidence"), 0.45),
            explanation=str(item.get("explanation") or ""),
        )


def _canonical_status(value: Any) -> str:
    status = str(value or "").strip().lower()
    return "cancelled" if status == "canceled" else status


def _order_marker_type(status: str, side: str) -> str:
    if status in {"submitted", "accepted"}:
        return f"{side}_order_submitted" if side in {"buy", "sell"} else "order_submitted"
    return {
        "signal_created": "signal_created",
        "prechecked": "prechecked",
        "needs_confirmation": "needs_confirmation",
        "confirmed": "confirmed",
        "partially_filled": "partial_fill",
        "cancel_requested": "cancel_requested",
        "cancelled": "cancelled",
        "rejected": "rejected",
        "expired": "expired",
        "failed": "failed",
        "risk_blocked": "risk_block",
    }.get(status, status or "order")


def _order_tooltip(order: dict[str, Any], status: str) -> str:
    reason = str(order.get("status_reason") or order.get("reason") or "")
    detail = f"{_side_cn(str(order.get('side') or ''))}委托 {_int(order.get('quantity'))} 股"
    return f"{_status_cn(status)}：{detail}" + (f"；{reason}" if reason else "")


def _status_cn(status: str) -> str:
    return {
        "signal_created": "信号已生成",
        "prechecked": "预检查通过",
        "risk_blocked": "风控拦截",
        "needs_confirmation": "等待人工确认",
        "confirmed": "已确认",
        "submitted": "已提交",
        "accepted": "券商已受理",
        "partially_filled": "部分成交",
        "filled": "全部成交",
        "cancel_requested": "已申请撤单",
        "cancelled": "已撤单",
        "rejected": "已拒单",
        "expired": "已过期",
        "failed": "提交失败",
    }.get(status, status or "订单状态未知")


def _side_cn(side: str) -> str:
    return {"buy": "买入", "sell": "卖出"}.get(str(side).lower(), "")


def _label(marker_type: str) -> str:
    return {
        "buy_order_submitted": "B委托",
        "sell_order_submitted": "S委托",
        "needs_confirmation": "待确认",
        "confirmed": "已确认",
        "partial_fill": "部分成交",
        "buy_fill": "B成交",
        "sell_fill": "S成交",
        "cancel_requested": "撤单中",
        "cancelled": "已撤单",
        "rejected": "拒单",
        "expired": "过期",
        "failed": "失败",
        "risk_block": "风控",
    }.get(marker_type, marker_type)


def _id(*parts: Any) -> str:
    return "mk-" + sha256("|".join(str(x or "") for x in parts).encode("utf-8")).hexdigest()[:16]


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except (TypeError, ValueError):
        return default


def _int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0
