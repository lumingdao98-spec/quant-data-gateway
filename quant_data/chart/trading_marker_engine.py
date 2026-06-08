from __future__ import annotations

from hashlib import sha256
from typing import Any

from .marker_models import ChartMarker


class TradingMarkerEngine:
    def from_order(self, order: dict[str, Any]) -> ChartMarker:
        status = str(order.get("status") or "")
        marker_type = {
            "submitted": f"{order.get('side','')}_order_submitted",
            "accepted": f"{order.get('side','')}_order_submitted",
            "needs_confirmation": "needs_confirmation",
            "rejected": "rejected",
            "risk_blocked": "risk_block",
        }.get(status, status or "order")
        ts = str(order.get("filled_at") or order.get("submitted_at") or order.get("created_at") or "")
        price = float(order.get("limit_price") or order.get("price") or 0.0)
        return ChartMarker(
            marker_id=_id(order.get("order_id"), marker_type, ts),
            symbol=str(order.get("symbol") or ""),
            mode=str(order.get("mode") or "paper"),
            session_id=str(order.get("session_id") or ""),
            timestamp=ts,
            price=price,
            marker_type=marker_type,
            side=str(order.get("side") or ""),
            quantity=int(order.get("quantity") or 0),
            label=_label(marker_type),
            tooltip=str(order.get("status_reason") or order.get("reason") or marker_type),
            order_id=str(order.get("order_id") or ""),
            signal_id=str(order.get("signal_id") or ""),
            provenance_id=str(order.get("provenance_id") or ""),
            confidence=0.85 if status in {"accepted", "filled"} else 0.55,
            explanation=str(order.get("status_reason") or ""),
        )

    def from_fill(self, fill: dict[str, Any], *, mode: str = "paper", session_id: str = "") -> ChartMarker:
        side = str(fill.get("side") or "")
        return ChartMarker(
            marker_id=_id(fill.get("fill_id"), side, fill.get("filled_at")),
            symbol=str(fill.get("symbol") or ""),
            mode=mode,
            session_id=session_id,
            timestamp=str(fill.get("filled_at") or fill.get("date") or ""),
            price=float(fill.get("price") or 0.0),
            marker_type=f"{side}_fill" if side else "fill",
            side=side,
            quantity=int(fill.get("quantity") or 0),
            label="B成交" if side == "buy" else "S成交",
            tooltip=f"{side} {fill.get('quantity')} @ {fill.get('price')}",
            order_id=str(fill.get("order_id") or ""),
            fill_id=str(fill.get("fill_id") or ""),
            confidence=0.95,
            explanation="成交标注",
        )

    def behavior_marker(self, symbol: str, item: dict[str, Any], *, mode: str = "analysis") -> ChartMarker:
        return ChartMarker(
            marker_id=_id(symbol, item.get("timestamp"), item.get("label")),
            symbol=symbol,
            mode=mode,
            session_id=str(item.get("session_id") or ""),
            timestamp=str(item.get("timestamp") or item.get("date") or ""),
            price=float(item.get("price") or 0.0),
            marker_type=str(item.get("marker_type") or "behavior_risk"),
            label=str(item.get("label") or "异常"),
            tooltip=str(item.get("tooltip") or item.get("explanation") or ""),
            confidence=float(item.get("confidence") or 0.45),
            explanation=str(item.get("explanation") or ""),
        )


def _id(*parts: Any) -> str:
    return "mk-" + sha256("|".join(str(x or "") for x in parts).encode("utf-8")).hexdigest()[:16]


def _label(marker_type: str) -> str:
    return {
        "buy_order_submitted": "B委托",
        "sell_order_submitted": "S委托",
        "needs_confirmation": "待确认",
        "rejected": "拒单",
        "risk_block": "风控",
    }.get(marker_type, marker_type)
