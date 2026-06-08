from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Any

from quant_data.data.data_contracts import DataSourceStatus


@dataclass(slots=True)
class FactorBundleV323:
    symbol: str
    decision_time: str
    values: dict[str, float] = field(default_factory=dict)
    sources: list[dict[str, Any]] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)
    stale_data: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "decision_time": self.decision_time,
            "values": dict(self.values),
            "sources": list(self.sources),
            "missing_data": list(self.missing_data),
            "stale_data": list(self.stale_data),
        }


class V323FactorEngine:
    """Converts available real snapshots into score dimensions without filling fake values."""

    def compute(
        self,
        symbol: str,
        *,
        decision_time: str,
        bars: list[dict[str, Any]] | None = None,
        quote: dict[str, Any] | None = None,
        fundamentals: dict[str, Any] | None = None,
        information: dict[str, Any] | None = None,
        fund_flow: dict[str, Any] | None = None,
        market_state: dict[str, Any] | None = None,
        behavior_risk: dict[str, Any] | None = None,
        data_sources: list[dict[str, Any] | DataSourceStatus] | None = None,
    ) -> FactorBundleV323:
        bars = list(bars or [])
        quote = quote or {}
        fundamentals = fundamentals or {}
        information = information or {}
        fund_flow = fund_flow or {}
        market_state = market_state or {}
        behavior_risk = behavior_risk or {}
        missing: list[str] = []
        stale: list[str] = []
        sources = [_source_dict(x) for x in (data_sources or [])]
        for src in sources:
            if src.get("stale"):
                stale.append(f"{src.get('source_name') or src.get('source_id')}缓存过期")
            missing.extend(src.get("missing_reasons") or [])

        values = {
            "technical_score": self._technical_score(bars, quote, missing),
            "fundamental_score": self._fundamental_score(fundamentals, missing),
            "information_score": self._information_score(information, missing),
            "fund_flow_score": self._fund_flow_score(fund_flow, quote, missing),
            "market_regime_score": self._market_score(market_state, missing),
            "behavior_risk_score": self._behavior_risk_score(behavior_risk, missing),
            "data_quality_score": self._data_quality_score(sources, missing, stale),
        }
        return FactorBundleV323(symbol=symbol, decision_time=decision_time, values=values, sources=sources, missing_data=list(dict.fromkeys(missing)), stale_data=list(dict.fromkeys(stale)))

    def _technical_score(self, bars: list[dict[str, Any]], quote: dict[str, Any], missing: list[str]) -> float:
        closes = [_num(x.get("close")) for x in bars if _num(x.get("close")) > 0]
        if len(closes) < 20:
            missing.append("K线不足20根，技术评分降为观察")
            return 50.0
        close = _num(quote.get("last") or quote.get("price")) or closes[-1]
        ma20 = mean(closes[-20:])
        ma60 = mean(closes[-60:]) if len(closes) >= 60 else ma20
        ret5 = close / closes[-6] - 1 if len(closes) > 5 and closes[-6] else 0.0
        score = 50 + (close / ma20 - 1) * 160 + (close / ma60 - 1) * 90 + ret5 * 120
        return _clip(score)

    def _fundamental_score(self, data: dict[str, Any], missing: list[str]) -> float:
        if not data:
            missing.append("基本面数据源缺失")
            return 50.0
        roe = _num(data.get("roe"))
        pb = _num(data.get("pb"))
        profit = _num(data.get("net_profit_growth") or data.get("profit_growth"))
        score = 50 + min(roe, 25) * 0.8 + max(-20, min(40, profit)) * 0.35 - max(0, pb - 8) * 1.5
        return _clip(score)

    def _information_score(self, data: dict[str, Any], missing: list[str]) -> float:
        if not data:
            missing.append("信息面快照缺失")
            return 50.0
        positive = _num(data.get("positive_count"))
        negative = _num(data.get("negative_count"))
        official = _num(data.get("official_count"))
        return _clip(50 + positive * 1.6 + official * 0.8 - negative * 3.5)

    def _fund_flow_score(self, data: dict[str, Any], quote: dict[str, Any], missing: list[str]) -> float:
        amount = _num(data.get("amount") or quote.get("amount"))
        volume_ratio = _num(data.get("volume_ratio") or quote.get("volume_ratio"))
        main_inflow = _num(data.get("main_inflow"))
        if not amount:
            missing.append("资金面成交额缺失")
        score = 50 + min(volume_ratio, 3) * 7 + max(-10, min(10, main_inflow / 100_000_000)) * 1.5
        return _clip(score)

    def _market_score(self, data: dict[str, Any], missing: list[str]) -> float:
        if not data:
            missing.append("大盘状态缺失")
            return 50.0
        return _clip(_num(data.get("sentiment_score"), 50) * 0.4 + _num(data.get("trend_score"), 50) * 0.35 + _num(data.get("breadth_score"), 50) * 0.25)

    def _behavior_risk_score(self, data: dict[str, Any], missing: list[str]) -> float:
        flags = data.get("risk_flags") or []
        if not data:
            missing.append("行为风险数据缺失")
        return _clip(len(flags) * 12 + _num(data.get("risk_score"), 0))

    def _data_quality_score(self, sources: list[dict[str, Any]], missing: list[str], stale: list[str]) -> float:
        if not sources:
            return 35.0
        score = 100 - len(missing) * 5 - len(stale) * 12
        return _clip(score)


def _source_dict(value: dict[str, Any] | DataSourceStatus) -> dict[str, Any]:
    return value.to_dict() if hasattr(value, "to_dict") else dict(value or {})


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "--"):
            return default
        return float(value)
    except Exception:
        return default


def _clip(value: float) -> float:
    return max(0.0, min(100.0, float(value)))
