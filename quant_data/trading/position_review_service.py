from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from typing import Any

from quant_data.persistence.trading_store import TradingStore

from .signal_fusion import SignalFusionEngine


def _number(value: Any) -> float | None:
    try:
        if value in (None, "", "--"):
            return None
        number = float(value)
        return number if number == number else None
    except (TypeError, ValueError):
        return None


def _stable_id(*parts: Any) -> str:
    raw = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return sha256(raw.encode("utf-8")).hexdigest()[:24]


class PositionReviewService:
    """Persist a daily, explainable review for held paper/live positions.

    Reviews never call a broker. Paper execution remains in the paper engine;
    live reviews can only recommend an order preview that still has to pass the
    normal risk gateway and confirmation queue.
    """

    def __init__(self, store: TradingStore | None = None, fusion: SignalFusionEngine | None = None) -> None:
        self.store = store or TradingStore()
        self.fusion = fusion or SignalFusionEngine()

    def decision_from_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        signal = self.fusion.fuse(
            symbol=str(payload.get("symbol") or ""),
            horizon=str(payload.get("horizon") or "position_review"),
            screening_score=_number(payload.get("screening_score")),
            daily_k_score=_number(payload.get("daily_k_score")),
            intraday_score=_number(payload.get("intraday_score")),
            fundamental_score=_number(payload.get("fundamental_score")),
            technical_score=_number(payload.get("technical_score")),
            information_score=_number(payload.get("information_score")),
            fund_flow_score=_number(payload.get("fund_flow_score")),
            market_score=_number(payload.get("market_score")),
            score_weights=payload.get("score_weights") if isinstance(payload.get("score_weights"), dict) else None,
            anomaly_score=_number(payload.get("anomaly_score")) or 0.0,
            info_negative_veto=bool(payload.get("info_negative_veto") or payload.get("major_negative_news")),
            technical_broken=bool(payload.get("technical_broken")),
            fundamental_poor=bool(payload.get("fundamental_poor")),
            evidence=list(payload.get("evidence") or []),
            data_freshness=dict(payload.get("data_freshness") or {}),
            missing_data=list(payload.get("missing_data") or []),
        )
        row = signal.to_dict()
        row["score_source"] = payload.get("score_source") or "position_review_recompute"
        row["market_event_context"] = dict(payload.get("market_event_context") or {})
        row["recent_information"] = dict(payload.get("recent_information") or {})
        return row

    def review(
        self,
        *,
        mode: str,
        session_id: str,
        symbol: str,
        position: dict[str, Any],
        decision: dict[str, Any],
        risk_controls: dict[str, Any] | None = None,
        decision_time: str = "",
    ) -> dict[str, Any]:
        now = decision_time or str(decision.get("timestamp") or datetime.now().isoformat(timespec="seconds"))
        review_date = now[:10]
        previous_rows = self.store.list("position_reviews", mode=mode, symbol=symbol, session_id=session_id, limit=2)
        previous = previous_rows[0] if previous_rows else {}
        score = _number(decision.get("final_score"))
        previous_score = _number(previous.get("final_score"))
        score_delta = round(score - previous_score, 2) if score is not None and previous_score is not None else None

        quantity = _number(position.get("quantity") or position.get("qty")) or 0.0
        avg_cost = _number(position.get("avg_cost") or position.get("cost_price") or position.get("avg_price")) or 0.0
        market_price = _number(position.get("market_price") or position.get("last_price") or decision.get("quote_price")) or 0.0
        market_value = _number(position.get("market_value"))
        if market_value is None:
            market_value = quantity * market_price
        unrealized = _number(position.get("unrealized_pnl"))
        if unrealized is None:
            unrealized = (market_price - avg_cost) * quantity if avg_cost and market_price else 0.0
        pnl_pct = _number(position.get("unrealized_pnl_pct") or position.get("pnl_pct"))
        if pnl_pct is None:
            pnl_pct = (market_price / avg_cost - 1.0) * 100 if avg_cost and market_price else 0.0

        risk = dict(risk_controls or {})
        stop_loss = abs(_number(risk.get("stop_loss_pct")) or 8.0)
        take_profit = abs(_number(risk.get("take_profit_pct")) or 18.0)
        missing = list(decision.get("missing_data") or [])
        freshness = dict(decision.get("data_freshness") or {})
        stale = bool(freshness.get("stale") or freshness.get("action") in {"block", "refresh_required"})
        if market_price <= 0:
            missing.append("持仓最新价缺失")
        blocking_missing_tokens = (
            "持仓最新价",
            "最新价",
            "实时行情",
            "行情快照",
            "quote",
            "daily_k",
            "日K",
            "K线",
            "近期信息",
            "recent_information",
            "realtime_decision_hydration_error",
        )
        blocking_missing = [
            str(reason)
            for reason in missing
            if any(token.lower() in str(reason).lower() for token in blocking_missing_tokens)
        ]

        action = "hold"
        reasons: list[str] = []
        if blocking_missing or stale:
            action = "manual_review"
            reasons.append("数据缺失或过期，禁止自动调整持仓")
        elif bool(decision.get("info_negative_veto")):
            action = "exit"
            reasons.append("重大负面信息触发退出复核")
        elif avg_cost > 0 and pnl_pct <= -stop_loss:
            action = "exit"
            reasons.append(f"浮亏 {pnl_pct:.2f}% 触发 {stop_loss:.2f}% 止损")
        elif avg_cost > 0 and pnl_pct >= take_profit:
            action = "reduce"
            reasons.append(f"浮盈 {pnl_pct:.2f}% 达到 {take_profit:.2f}% 分批止盈线")
        elif score is not None and score <= 45:
            action = "exit"
            reasons.append(f"综合交易分降至 {score:.2f}")
        elif score is not None and score < 55:
            action = "reduce"
            reasons.append(f"综合交易分 {score:.2f} 进入减仓观察区")
        elif score_delta is not None and score_delta <= -8:
            action = "reduce"
            reasons.append(f"较上次复核下降 {abs(score_delta):.2f} 分")
        else:
            reasons.append("评分、事件和持仓风险未触发退出条件")

        action_cn = {
            "hold": "继续持有/观察",
            "reduce": "减仓复核",
            "exit": "退出复核",
            "manual_review": "人工复核",
        }[action]
        live = mode == "live"
        review = {
            "review_id": _stable_id("position-review", mode, session_id, symbol, review_date),
            "mode": mode,
            "mode_cn": "真实交易" if live else "实时模拟",
            "session_id": session_id,
            "symbol": symbol,
            "name": decision.get("name") or position.get("name") or symbol,
            "review_date": review_date,
            "decision_time": now,
            "created_at": now,
            "quantity": quantity,
            "available_quantity": _number(position.get("available_quantity")) if position.get("available_quantity") is not None else quantity,
            "avg_cost": round(avg_cost, 6),
            "market_price": round(market_price, 6),
            "market_value": round(market_value, 4),
            "unrealized_pnl": round(unrealized, 4),
            "unrealized_pnl_pct": round(pnl_pct, 4),
            "final_score": score,
            "previous_score": previous_score,
            "score_delta": score_delta,
            "action": action,
            "action_cn": action_cn,
            "reasons": reasons,
            "stop_loss_pct": stop_loss,
            "take_profit_pct": take_profit,
            "score_breakdown": dict(decision.get("score_breakdown") or {}),
            "market_event_context": dict(decision.get("market_event_context") or {}),
            "recent_information": dict(decision.get("recent_information") or {}),
            "evidence": list(dict.fromkeys(list(decision.get("evidence") or []) + reasons)),
            "missing_data": list(dict.fromkeys(missing)),
            "blocking_missing_data": list(dict.fromkeys(blocking_missing)),
            "data_freshness": freshness,
            "execution_allowed": False,
            "execution_policy": "仅生成实盘确认建议，必须重新经过风控与人工确认" if live else "模拟订单仍由实时模拟内核和风控网关执行",
            "needs_confirmation": live and action in {"reduce", "exit"},
            "broker_submitted": False,
            "truth_boundary": "持仓复核不会直接调用券商，也不会把缺失数据补成中性分。",
        }
        self.store.put(
            "position_reviews",
            review,
            mode=mode,
            symbol=symbol,
            session_id=session_id,
            record_id=review["review_id"],
        )
        return review

    def list_reviews(self, *, mode: str = "", session_id: str = "", symbol: str = "", limit: int = 200) -> list[dict[str, Any]]:
        return self.store.list(
            "position_reviews",
            mode=mode,
            session_id=session_id,
            symbol=symbol,
            limit=limit,
        )
