from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from quant_data.models import OrderBook, OrderBookLevel


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _depth(levels: list[OrderBookLevel]) -> float:
    return sum(max(0.0, _num(x.volume)) for x in levels)


@dataclass(slots=True)
class _BookSnapshot:
    ts: datetime
    best_bid: float | None
    best_ask: float | None
    bid_depth: float
    ask_depth: float


class OrderBookBehaviorService:
    """Low-confidence public order book heuristics.

    The app only receives public L1/five-level snapshots, not Level-2 queue
    events. These signals are deliberately worded as observations.
    """

    def __init__(self) -> None:
        self._history: dict[str, list[_BookSnapshot]] = {}

    def analyze(
        self,
        book: OrderBook | None,
        *,
        symbol: str = "",
        skipped_external: bool = False,
        note: str = "",
    ) -> dict[str, Any]:
        symbol = symbol or getattr(book, "symbol", "") or ""
        asks = list(getattr(book, "asks", []) or [])
        bids = list(getattr(book, "bids", []) or [])
        bid_depth = _depth(bids)
        ask_depth = _depth(asks)
        best_bid = _num(bids[0].price, 0.0) if bids else 0.0
        best_ask = _num(asks[0].price, 0.0) if asks else 0.0
        spread_pct = ((best_ask - best_bid) / best_bid * 100.0) if best_bid and best_ask and best_ask >= best_bid else None
        total_depth = bid_depth + ask_depth
        imbalance_pct = ((bid_depth - ask_depth) / total_depth * 100.0) if total_depth else None

        signals: list[str] = []
        risk_flags: list[str] = []
        evidence: list[str] = []

        if skipped_external:
            signals.append("休市/非交易时段仅使用缓存盘口；不做实时盘口结论")
        if note:
            evidence.append(note)
        if not asks or not bids:
            signals.append("公开源未返回完整五档，只能显示委比/委差或缓存状态")

        if imbalance_pct is not None:
            evidence.append(f"五档买卖深度偏斜 {imbalance_pct:.1f}%")
            if imbalance_pct >= 35:
                signals.append("买盘深度明显占优，可能存在承接/吸筹观察")
            elif imbalance_pct <= -35:
                signals.append("卖盘深度明显占优，可能存在压单/抛压观察")

        if spread_pct is not None:
            evidence.append(f"买卖一价差 {spread_pct:.3f}%")
            if spread_pct >= 0.8:
                risk_flags.append("买卖价差偏大，成交价格不确定性上升")

        if bids:
            avg_bid = bid_depth / max(1, len(bids))
            big_bids = [i + 1 for i, x in enumerate(bids) if _num(x.volume) >= avg_bid * 2.5 and _num(x.volume) > 0]
            if big_bids:
                signals.append(f"买{','.join(map(str, big_bids[:3]))}存在相对大挂单，偏承接观察")
        if asks:
            avg_ask = ask_depth / max(1, len(asks))
            big_asks = [i + 1 for i, x in enumerate(asks) if _num(x.volume) >= avg_ask * 2.5 and _num(x.volume) > 0]
            if big_asks:
                signals.append(f"卖{','.join(map(str, big_asks[:3]))}存在相对大挂单，偏压单观察")

        prev_flags = self._compare_previous(symbol, best_bid or None, best_ask or None, bid_depth, ask_depth)
        risk_flags.extend(prev_flags)

        order_ratio = getattr(book, "order_ratio", None) if book else None
        if order_ratio is not None:
            ratio = _num(order_ratio)
            evidence.append(f"委比 {ratio:.2f}%")
            if ratio >= 45:
                signals.append("委比偏强，买盘主动性观察")
            elif ratio <= -45:
                signals.append("委比偏弱，卖盘主动性观察")

        if not signals and not risk_flags:
            signals.append("盘口暂未出现明显偏斜；公开快照不足以判断主力行为")

        return {
            "confidence": "low",
            "requires_level2": True,
            "summary": "；".join(signals[:3]),
            "signals": signals[:8],
            "risk_flags": risk_flags[:8],
            "evidence": evidence[:8],
            "metrics": {
                "bid_depth": round(bid_depth, 6),
                "ask_depth": round(ask_depth, 6),
                "imbalance_pct": round(imbalance_pct, 4) if imbalance_pct is not None else None,
                "spread_pct": round(spread_pct, 6) if spread_pct is not None else None,
            },
            "limitations": [
                "公开五档/L1快照没有逐笔委托队列，不能确认真实撤单、对倒或主力身份",
                "虚假撤单、吸筹和诱多诱空只能作为低置信度观察，需Level-2逐笔/委托队列复核",
            ],
        }

    def _compare_previous(
        self,
        symbol: str,
        best_bid: float | None,
        best_ask: float | None,
        bid_depth: float,
        ask_depth: float,
    ) -> list[str]:
        if not symbol:
            return []
        now = datetime.now()
        snap = _BookSnapshot(now, best_bid, best_ask, bid_depth, ask_depth)
        rows = self._history.setdefault(symbol, [])
        flags: list[str] = []
        if rows:
            prev = rows[-1]
            same_bid = prev.best_bid and best_bid and abs(prev.best_bid - best_bid) < 1e-9
            same_ask = prev.best_ask and best_ask and abs(prev.best_ask - best_ask) < 1e-9
            if same_bid and prev.bid_depth > 0 and bid_depth < prev.bid_depth * 0.35:
                flags.append("买盘深度短时大幅消失，疑似挂撤变化，需Level-2确认")
            if same_ask and prev.ask_depth > 0 and ask_depth < prev.ask_depth * 0.35:
                flags.append("卖盘深度短时大幅消失，疑似撤压/挂撤变化，需Level-2确认")
        rows.append(snap)
        if len(rows) > 8:
            del rows[:-8]
        return flags
