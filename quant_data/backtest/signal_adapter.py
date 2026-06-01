from __future__ import annotations

from typing import Any

from .data_loader import date_text, field_value, number
from .models import BacktestConfig, StrategySignal


class SignalAdapter:
    """Convert screener rows, factor rows and event filters into strategy signals."""

    def score_rank_rebalance(self, rows: list[dict[str, Any]], date: str, config: BacktestConfig | None = None) -> list[StrategySignal]:
        cfg = config or BacktestConfig()
        valid: list[dict[str, Any]] = []
        for row in rows:
            symbol = str(row.get("symbol") or row.get("code") or "").strip()
            grade = str(row.get("grade") or row.get("level") or "")
            risk_flags = list(row.get("risk_flags") or row.get("risk_tags") or [])
            if not symbol or grade.startswith("D") or grade.startswith("E"):
                continue
            if row.get("suspended") or row.get("is_st") or row.get("limit_up"):
                continue
            if any("高风险" in str(x) or "退市" in str(x) for x in risk_flags):
                continue
            score = number(row.get("score", row.get("total_score")))
            if score < cfg.buy_score:
                continue
            valid.append({**row, "symbol": symbol, "score": score, "risk_flags": risk_flags})
        valid.sort(key=lambda x: (number(x.get("score")), number(x.get("amount"))), reverse=True)
        picked = valid[: max(1, cfg.max_positions)]
        score_sum = sum(max(1.0, number(x.get("score"))) for x in picked) or 1.0
        signals: list[StrategySignal] = []
        for row in picked:
            score = number(row.get("score"))
            target = min(cfg.max_single_position_pct, cfg.position_pct * (max(1.0, score) / score_sum))
            signals.append(
                StrategySignal(
                    symbol=row["symbol"],
                    date=date,
                    action="buy",
                    score=round(score, 4),
                    strength=round(score / 100, 4),
                    target_weight=round(target, 6),
                    price=row.get("price") or row.get("last"),
                    reason=f"筛选评分 {score:.1f} 达到买入阈值 {cfg.buy_score:.1f}",
                    source="score_rank_rebalance",
                    grade=str(row.get("grade") or ""),
                    risk_flags=list(row.get("risk_flags") or []),
                    features=dict(row),
                    snapshot_id=cfg.screener_snapshot_id or row.get("snapshot_id"),
                )
            )
        return signals

    def factor_rule_strategy(self, rows: list[Any], config: BacktestConfig | None = None) -> list[StrategySignal]:
        cfg = config or BacktestConfig()
        signals: list[StrategySignal] = []
        for row in rows:
            symbol = str(field_value(row, "symbol", "")).strip()
            close = number(field_value(row, "close"))
            ma20 = number(field_value(row, "ma20"))
            ma60 = number(field_value(row, "ma60"))
            rsi = number(field_value(row, "rsi14", field_value(row, "rsi")))
            volume_ratio = number(field_value(row, "volume_ratio"), 1.0)
            d = date_text(field_value(row, "ts", field_value(row, "date", "")))
            if not symbol or close <= 0:
                continue
            action = "hold"
            score = 50.0
            reasons: list[str] = []
            if ma20 and close > ma20:
                score += 12
                reasons.append("收盘价站上 MA20")
            if ma60 and close > ma60:
                score += 8
                reasons.append("收盘价站上 MA60")
            if 45 <= rsi <= 68:
                score += 8
                reasons.append("RSI 处于趋势健康区间")
            elif rsi >= 78:
                score -= 12
                reasons.append("RSI 过热")
            if volume_ratio >= 1.5:
                score += 6
                reasons.append("成交量放大")
            if score >= cfg.buy_score:
                action = "buy"
            elif score <= cfg.sell_score:
                action = "sell"
            if action != "hold":
                signals.append(
                    StrategySignal(
                        symbol=symbol,
                        date=d,
                        action=action,
                        score=round(score, 4),
                        strength=round(abs(score - 50) / 50, 4),
                        target_weight=cfg.max_single_position_pct if action == "buy" else 0.0,
                        price=close,
                        reason="；".join(reasons) or "因子规则触发",
                        source="factor_rule_strategy",
                    )
                )
        return signals

    def event_risk_filter(self, signals: list[StrategySignal], events: dict[str, list[dict[str, Any]]] | None = None) -> list[StrategySignal]:
        events = events or {}
        filtered: list[StrategySignal] = []
        for signal in signals:
            symbol_events = events.get(signal.symbol, [])
            risk_text = "；".join(str(x.get("title") or x.get("tag") or x) for x in symbol_events)
            high_risk = any(str(x.get("severity") or "").lower() in {"high", "fatal"} for x in symbol_events)
            high_risk = high_risk or any(word in risk_text for word in ["减持", "立案", "退市", "暴雷", "监管"])
            if high_risk and signal.action == "buy":
                filtered.append(
                    StrategySignal(
                        symbol=signal.symbol,
                        date=signal.date,
                        action="avoid",
                        score=max(0.0, signal.score - 20.0),
                        strength=signal.strength,
                        target_weight=0.0,
                        price=signal.price,
                        reason=f"事件风险过滤：{risk_text[:80]}",
                        source="event_risk_filter",
                        grade=signal.grade,
                        risk_flags=[*signal.risk_flags, "event_risk"],
                        features=signal.features,
                        snapshot_id=signal.snapshot_id,
                    )
                )
            else:
                filtered.append(signal)
        return filtered
