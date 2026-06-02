from __future__ import annotations

from dataclasses import asdict, dataclass, field
from statistics import mean
from typing import Any

from quant_data.backtest.data_loader import date_text, field_value, number

from .score_provenance import FactorValue


@dataclass(slots=True)
class FactorBundle:
    symbol: str
    asof_time: str
    factors: list[FactorValue] = field(default_factory=list)
    score: float = 50.0
    source_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["factors"] = [x.to_dict() for x in self.factors]
        return data


class FactorEngine:
    """Compute PIT technical factors with metadata for score provenance."""

    def compute(self, symbol: str, bars: list[Any], *, asof_time: str | None = None) -> FactorBundle:
        rows = list(bars or [])
        if not rows:
            return FactorBundle(symbol=symbol, asof_time=asof_time or "", factors=[], source_refs=["missing:bars"])
        closes = [number(field_value(x, "close")) for x in rows]
        highs = [number(field_value(x, "high"), number(field_value(x, "close"))) for x in rows]
        lows = [number(field_value(x, "low"), number(field_value(x, "close"))) for x in rows]
        volumes = [number(field_value(x, "volume")) for x in rows]
        last = rows[-1]
        close = closes[-1]
        asof = asof_time or date_text(field_value(last, "ts", field_value(last, "date", "")))
        ma20 = _ma(closes, 20)
        ma60 = _ma(closes, 60)
        vol20 = _ma(volumes, 20)
        hi60 = max(closes[-60:]) if closes else close
        lo60 = min(closes[-60:]) if closes else close
        pos60 = (close - lo60) / max(hi60 - lo60, 1e-9) * 100
        rsi = _rsi(closes[-15:])
        ret5 = _ret(closes, 5)
        ret20 = _ret(closes, 20)
        trend_score = _clip(50 + ((close / ma20 - 1) * 180 if ma20 else 0) + ((close / ma60 - 1) * 120 if ma60 else 0))
        momentum_score = _clip(50 + ret5 * 2.2 + ret20 * 0.8 + (rsi - 50) * 0.35)
        volume_score = _clip(50 + ((volumes[-1] / vol20 - 1) * 24 if vol20 else 0))
        structure_score = _clip(70 - abs(pos60 - 45) * 0.8)
        risk_penalty = _clip(max(0.0, (pos60 - 82) * 1.3) + (max(0.0, rsi - 76) * 1.1))
        specs = [
            ("trend_score", trend_score, 34.0, "technical", "close/MA20/MA60"),
            ("momentum_score", momentum_score, 25.0, "technical", "ret5/ret20/RSI"),
            ("volume_score", volume_score, 19.0, "volume", "volume/MA20"),
            ("structure_score", structure_score, 22.0, "structure", "60日区间位置"),
            ("risk_penalty", 50 - risk_penalty, -45.0, "risk", "高位/过热扣分"),
        ]
        factors = [
            FactorValue(
                factor_id=f"v322-{key}",
                symbol=symbol,
                asof_time=asof,
                factor_key=key,
                raw_value=round(raw, 6),
                normalized_value=round(raw, 6),
                weight=weight,
                source_refs=[source],
                available_at=asof,
                group=group,
            )
            for key, raw, weight, group, source in specs
        ]
        score = _clip(trend_score * 0.34 + momentum_score * 0.25 + volume_score * 0.19 + structure_score * 0.22 - risk_penalty * 0.45)
        return FactorBundle(symbol=symbol, asof_time=asof, factors=factors, score=round(score, 4), source_refs=["PIT:bars"])


def _ma(values: list[float], period: int) -> float:
    if not values:
        return 0.0
    window = values[-min(period, len(values)) :]
    return mean(window) if window else 0.0


def _ret(values: list[float], period: int) -> float:
    if len(values) <= period or values[-period - 1] == 0:
        return 0.0
    return (values[-1] / values[-period - 1] - 1) * 100


def _rsi(values: list[float]) -> float:
    if len(values) < 2:
        return 50.0
    gains = []
    losses = []
    for a, b in zip(values, values[1:]):
        delta = b - a
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))
    avg_gain = mean(gains) if gains else 0.0
    avg_loss = mean(losses) if losses else 0.0
    if avg_loss == 0:
        return 100.0 if avg_gain else 50.0
    return 100 - 100 / (1 + avg_gain / avg_loss)


def _clip(value: float) -> float:
    return max(0.0, min(100.0, float(value)))
