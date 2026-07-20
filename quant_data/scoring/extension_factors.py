from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ExtensionFactorResult:
    values: dict[str, float] = field(default_factory=dict)
    confidence: dict[str, float] = field(default_factory=dict)
    evidence: dict[str, list[str]] = field(default_factory=dict)
    missing_data: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class V324ExtensionFactorEngine:
    """Optional evidence factors. Missing inputs remain missing and never become synthetic zeroes."""

    def compute(
        self,
        *,
        macro: dict[str, Any] | None = None,
        sector: dict[str, Any] | None = None,
        earnings: dict[str, Any] | None = None,
        ipo: dict[str, Any] | None = None,
        fund_flow: dict[str, Any] | None = None,
    ) -> ExtensionFactorResult:
        macro = dict(macro or {})
        sector = dict(sector or {})
        earnings = dict(earnings or {})
        ipo = dict(ipo or {})
        fund_flow = dict(fund_flow or {})
        result = ExtensionFactorResult()
        self._set(result, "macro_liquidity_stress", _optional_weighted(macro, (("liquidity_stress", 0.55), ("rates_stress", 0.25), ("credit_stress", 0.20))), ["宏观流动性", "利率", "信用"])
        self._set(result, "global_semis_drawdown", _optional_number(sector, "global_semis_drawdown", "semis_drawdown_pct", "semiconductor_drawdown_pct"), ["全球半导体板块回撤"])
        self._set(result, "ipo_liquidity_shock", _optional_number(ipo, "liquidity_shock_score", "ipo_shock_score", "fund_diversion_score"), ["IPO 资金分流"])
        surprise = _earnings_surprise(earnings)
        self._set(result, "earnings_surprise", surprise, ["实际净利润", "一致预期"])
        self._set(result, "guidance_delta", _optional_number(earnings, "guidance_delta_pct"), ["业绩指引变化"])
        self._set(result, "northbound_flow_regime", _optional_number(fund_flow, "northbound_flow_regime", "northbound_regime_score", "northbound_score"), ["北向资金状态"])
        self._set(result, "sector_sentiment_velocity", _optional_number(sector, "sentiment_velocity", "strength_velocity"), ["板块强度变化速度"])
        self._set(result, "competitor_listing_pressure", _optional_number(ipo, "competitor_listing_pressure"), ["竞品上市供给压力"])
        return result

    def _set(self, result: ExtensionFactorResult, key: str, value: float | None, evidence: list[str]) -> None:
        if value is None:
            result.missing_data.append(f"{key} 数据缺失")
            return
        result.values[key] = round(float(value), 6)
        result.confidence[key] = 0.75
        result.evidence[key] = evidence


def _optional_number(data: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        if data.get(key) not in (None, "", "--"):
            try:
                return float(data[key])
            except Exception:
                return None
    return None


def _optional_weighted(data: dict[str, Any], fields: tuple[tuple[str, float], ...]) -> float | None:
    values: list[tuple[float, float]] = []
    for key, weight in fields:
        value = _optional_number(data, key)
        if value is not None:
            values.append((value, weight))
    if not values:
        return None
    weight_sum = sum(weight for _, weight in values)
    return sum(value * weight for value, weight in values) / weight_sum if weight_sum else None


def _earnings_surprise(data: dict[str, Any]) -> float | None:
    direct = _optional_number(data, "earnings_surprise_pct")
    if direct is not None:
        return direct
    actual = _optional_number(data, "net_profit", "actual_profit")
    consensus = _optional_number(data, "consensus_profit")
    if actual is None or consensus in (None, 0):
        return None
    return (actual - consensus) / abs(consensus) * 100
