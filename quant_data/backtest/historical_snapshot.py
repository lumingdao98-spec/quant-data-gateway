from __future__ import annotations

from typing import Any

from .data_loader import date_text, field_value, number


class HistoricalScreenerSnapshotBuilder:
    """Build point-in-time screener-like rows from historical bars only."""

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
