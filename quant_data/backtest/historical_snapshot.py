from __future__ import annotations

from hashlib import sha256
from typing import Any

from .data_loader import date_text, field_value, number
from quant_data.factors.factor_engine import FactorEngine
from quant_data.research.market_state_engine import MarketStateEngine
from quant_data.research.stock_classifier import StockClassifier
from quant_data.research.strategy_suitability import StrategySuitabilityEngine
from quant_data.strategy.strategy_family import get_strategy_execution_profile


class HistoricalScreenerSnapshotBuilder:
    """Build point-in-time screener-like rows from historical bars only."""

    def __init__(self) -> None:
        self.factor_engine = FactorEngine()
        self.market_engine = MarketStateEngine()
        self.classifier = StockClassifier()
        self.suitability = StrategySuitabilityEngine()

    def build(self, symbol: str, bars: list[Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        closes: list[float] = []
        volumes: list[float] = []
        for bar in bars:
            close = number(field_value(bar, "close"))
            volume = number(field_value(bar, "volume"))
            closes.append(close)
            volumes.append(volume)
            if len(closes) < 20 or close <= 0:
                continue
            ma20 = sum(closes[-20:]) / 20
            ma60 = sum(closes[-60:]) / min(len(closes), 60)
            vol20 = sum(volumes[-20:]) / 20
            trend = _clip(50 + (close / ma20 - 1) * 180 + (close / ma60 - 1) * 120)
            volume_score = _clip(50 + (volume / vol20 - 1) * 22) if vol20 else 50.0
            hi60 = max(closes[-60:])
            lo60 = min(closes[-60:])
            pos60 = (close - lo60) / max(hi60 - lo60, 1e-9)
            structure = _clip(70 - abs(pos60 - 0.45) * 70)
            behavior_risk = _clip(max(0.0, (pos60 - 0.82) * 120))
            technical = trend * 0.45 + volume_score * 0.22 + structure * 0.33
            final = _clip(technical - behavior_risk * 0.45)
            rows.append(
                {
                    "symbol": symbol,
                    "date": date_text(field_value(bar, "ts", field_value(bar, "date", ""))),
                    "technical_score": round(technical, 2),
                    "volume_score": round(volume_score, 2),
                    "structure_score": round(structure, 2),
                    "behavior_risk": round(behavior_risk, 2),
                    "final_backtest_score": round(final, 2),
                    "score": round(final, 2),
                    "grade": _grade(final),
                    "reason": "PIT日K快照：只使用当日及以前量价数据，不补未来信息面/基本面。",
                }
            )
        return rows

    def build_historical_snapshot(
        self,
        trade_date: Any,
        decision_time: Any,
        universe: list[str] | None = None,
        *,
        bars_by_symbol: dict[str, list[Any]] | None = None,
        market_inputs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        bars_by_symbol = bars_by_symbol or {}
        symbols = universe or sorted(bars_by_symbol)
        asof = str(decision_time)
        market_state = self.market_engine.compute(market_inputs or {}, asof_time=asof)
        rows: list[dict[str, Any]] = []
        source_refs: list[str] = ["PIT:bars"]
        for symbol in symbols:
            history = [x for x in bars_by_symbol.get(symbol, []) if date_text(field_value(x, "ts", field_value(x, "date", ""))) <= str(trade_date)[:10]]
            if not history:
                continue
            row = (self.build(symbol, history)[-1:] or [{}])[0]
            factors = self.factor_engine.compute(symbol, history, asof_time=asof)
            profile = self.classifier.classify(symbol, {**row, "technical_score": factors.score})
            suitability = self.suitability.evaluate(symbol, asof, market_state, profile, factors, {})
            execution_profile = get_strategy_execution_profile(suitability.strategy_family)
            row.update(
                {
                    "symbol": symbol,
                    "asof_time": asof,
                    "snapshot_trade_date": str(trade_date)[:10],
                    "strategy_family": suitability.strategy_family,
                    "strategy_profile_hash": execution_profile.profile_hash,
                    "policy_hash": execution_profile.policy_hash,
                    "execution_profile_version": execution_profile.profile_version,
                    "suitability_reason": "；".join(suitability.reasons or suitability.warnings),
                    "factor_score": factors.score,
                    "market_regime": market_state.market_regime,
                    "source_refs": sorted(set(source_refs + factors.source_refs)),
                }
            )
            rows.append(row)
        digest = sha256(repr([(r.get("symbol"), r.get("score"), r.get("strategy_family")) for r in rows]).encode("utf-8")).hexdigest()[:16]
        return {
            "snapshot_id": f"snap-{str(trade_date)[:10]}-{digest}",
            "trade_date": str(trade_date)[:10],
            "decision_time": asof,
            "asof_time": asof,
            "rows": rows,
            "row_count": len(rows),
            "market_state": market_state.to_dict(),
            "source_refs": source_refs,
            "immutable_hash": digest,
            "pit_note": "只使用 trade_date/decision_time 之前可见的 bars；未指定的财报/公告/资金流以缺失处理。",
        }


def _clip(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _grade(score: float) -> str:
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    return "D"
