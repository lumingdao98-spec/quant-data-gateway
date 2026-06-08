from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class StockProfileV323:
    symbol: str
    stock_type: str = "unknown"
    industry: str = ""
    concepts: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    confidence: float = 0.45

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StockClassifierV323:
    def classify(self, symbol: str, fundamentals: dict[str, Any] | None = None, quote: dict[str, Any] | None = None) -> StockProfileV323:
        fundamentals = fundamentals or {}
        quote = quote or {}
        risks: list[str] = []
        text = f"{symbol} {fundamentals.get('name','')} {fundamentals.get('industry','')} {' '.join(fundamentals.get('concepts') or [])}"
        if quote.get("is_st") or fundamentals.get("is_st") or "ST" in text:
            risks.append("ST/退市风险")
        if symbol.startswith(("510", "159", "512", "588", "515")):
            kind = "etf_index"
        elif risks:
            kind = "high_risk"
        elif any(k in text for k in ["红利", "银行", "公用事业"]):
            kind = "dividend_low_vol"
        elif any(k in text for k in ["周期", "煤炭", "钢铁", "有色", "光伏", "新能源"]):
            kind = "cyclical"
        elif any(k in text for k in ["AI", "机器人", "芯片", "算力", "题材"]):
            kind = "short_theme"
        elif _num(fundamentals.get("roe")) >= 12 and _num(fundamentals.get("net_profit_growth")) >= 5:
            kind = "long_term_compounder"
        elif _num(fundamentals.get("net_profit_growth")) < -20:
            kind = "turnaround"
        else:
            kind = "unknown"
        return StockProfileV323(
            symbol=symbol,
            stock_type=kind,
            industry=str(fundamentals.get("industry") or ""),
            concepts=list(fundamentals.get("concepts") or []),
            risk_flags=risks,
            confidence=0.72 if kind != "unknown" else 0.38,
        )


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0
