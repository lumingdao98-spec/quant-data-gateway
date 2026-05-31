from __future__ import annotations

from dataclasses import dataclass

from quant_data.indicators import moving_average
from quant_data.models import Bar, Quote


def _n(x, d: float = 0.0) -> float:
    try:
        return float(x) if x is not None else d
    except Exception:
        return d


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class MarketIndexSpec:
    key: str
    name: str
    symbol: str
    weight: float


MARKET_INDEX_SPECS = [
    MarketIndexSpec("shanghai", "上证指数", "sh000001", 0.25),
    MarketIndexSpec("sz_component", "深成指", "sz399001", 0.20),
    MarketIndexSpec("chinext", "创业板指", "sz399006", 0.25),
    MarketIndexSpec("csi300", "沪深300", "sh000300", 0.20),
    MarketIndexSpec("star50", "科创50", "sh000688", 0.10),
]


class MarketRegimeService:
    """大盘环境评分。

    100分不是预测胜率，也不是买入信号。它是市场背景温度：
    - 指数趋势占主导，避免小样本涨跌家数把分数顶满。
    - 市场宽度只做辅证，表示上涨家数、强弱家数是否扩散。
    """

    index_specs = MARKET_INDEX_SPECS

    def analyze_quotes(self, quotes: list[Quote]) -> dict:
        if not quotes:
            return {
                "regime": "unknown",
                "score": 50,
                "breadth_score": 50,
                "basis": "无市场快照；宽度分保持中性。",
                "score_definition": "50为中性，>60偏暖，<45偏弱；单一候选池样本不足时会自动收缩到50附近。",
                "sample_count": 0,
            }
        up = sum(1 for q in quotes if _n(q.change_pct) > 0)
        down = sum(1 for q in quotes if _n(q.change_pct) < 0)
        strong = sum(1 for q in quotes if _n(q.change_pct) >= 5)
        weak = sum(1 for q in quotes if _n(q.change_pct) <= -5)
        amount = sum(_n(q.amount) for q in quotes)
        total = max(1, up + down)
        up_ratio = up / total
        strong_ratio = strong / total
        weak_ratio = weak / total
        raw = 50 + (up_ratio - 0.5) * 60 + (strong_ratio - weak_ratio) * 35
        confidence = min(1.0, total / 80.0)
        score = 50 + (raw - 50) * confidence
        score = round(_clamp(score, 5, 95), 2)
        regime = self._label(score)
        return {
            "regime": regime,
            "score": score,
            "breadth_score": score,
            "up_count": up,
            "down_count": down,
            "up_ratio": round(up_ratio, 3),
            "strong_count": strong,
            "weak_count": weak,
            "strong_ratio": round(strong_ratio, 3),
            "weak_ratio": round(weak_ratio, 3),
            "sample_count": total,
            "sample_amount": amount,
            "confidence": round(confidence, 2),
            "basis": "市场宽度分：50为中性，涨跌家数扩散加/减分，强弱家数按比例修正；样本不足会收缩到中性。",
            "score_definition": "宽度分不是大盘总分；正式大盘分还需要上证、深成指、创业板、沪深300等指数趋势确认。",
        }

    def analyze_market(self, quotes: list[Quote], index_bars: dict[str, list[Bar]] | None = None) -> dict:
        breadth = self.analyze_quotes(quotes)
        index_items = []
        total_weight = 0.0
        weighted = 0.0
        index_bars = index_bars or {}
        for spec in self.index_specs:
            bars = index_bars.get(spec.key) or index_bars.get(spec.symbol) or []
            item = self._score_index(spec, bars)
            if not item:
                continue
            index_items.append(item)
            total_weight += spec.weight
            weighted += float(item["score"]) * spec.weight
        if total_weight > 0:
            index_score = weighted / total_weight
            score = index_score * 0.70 + float(breadth.get("breadth_score", 50)) * 0.30
            basis = "大盘总分=70%指数趋势 + 30%市场宽度；指数覆盖上证、深成指、创业板、沪深300、科创50，缺失指数按可用权重重算。"
            confidence = "high" if len(index_items) >= 4 and int(breadth.get("sample_count") or 0) >= 80 else "medium"
        else:
            index_score = None
            sample_count = int(breadth.get("sample_count") or 0)
            shrink = min(1.0, sample_count / 80.0)
            score = 50 + (float(breadth.get("breadth_score", 50)) - 50) * shrink
            basis = "未取到指数K线，本次仅用市场宽度兜底；样本不足时不会把大盘分顶满。"
            confidence = "low"
        score = round(_clamp(score, 5, 95), 2)
        return {
            **breadth,
            "score": score,
            "regime": self._label(score),
            "index_score": round(index_score, 2) if index_score is not None else None,
            "breadth_score": breadth.get("breadth_score", breadth.get("score")),
            "indices": index_items,
            "index_count": len(index_items),
            "confidence": confidence,
            "basis": basis,
            "score_definition": "大盘环境分：50中性；60以上偏暖；72以上强势；45以下偏弱。它只影响筛选排序小幅调分，不构成交易信号。",
        }

    def _score_index(self, spec: MarketIndexSpec, bars: list[Bar]) -> dict | None:
        closes = [float(b.close or 0) for b in bars if b.close and b.close > 0]
        if len(closes) < 25:
            return None
        last = closes[-1]
        ma5 = moving_average(closes, 5)
        ma20 = moving_average(closes, 20)
        ma60 = moving_average(closes, 60)
        ret1 = (closes[-1] / closes[-2] - 1) * 100 if len(closes) >= 2 and closes[-2] else 0.0
        ret5 = (closes[-1] / closes[-6] - 1) * 100 if len(closes) >= 6 and closes[-6] else 0.0
        ret20 = (closes[-1] / closes[-21] - 1) * 100 if len(closes) >= 21 and closes[-21] else 0.0
        ma20_dev = (last / ma20 - 1) * 100 if ma20 else 0.0
        ma60_dev = (last / ma60 - 1) * 100 if ma60 else 0.0
        trend = 0.0
        trend += max(-16, min(16, ma20_dev * 3.0))
        trend += max(-12, min(12, ma60_dev * 1.8))
        trend += max(-10, min(10, ret5 * 1.6))
        trend += max(-8, min(8, ret20 * 0.8))
        trend += max(-6, min(6, ret1 * 2.0))
        if ma5 and ma20 and ma5 > ma20:
            trend += 4
        elif ma5 and ma20 and ma5 < ma20:
            trend -= 4
        score = round(_clamp(50 + trend, 5, 95), 2)
        return {
            "key": spec.key,
            "name": spec.name,
            "symbol": spec.symbol,
            "score": score,
            "regime": self._label(score),
            "last": round(last, 4),
            "ret1_pct": round(ret1, 2),
            "ret5_pct": round(ret5, 2),
            "ret20_pct": round(ret20, 2),
            "ma20_dev_pct": round(ma20_dev, 2),
            "ma60_dev_pct": round(ma60_dev, 2),
            "bars": len(closes),
        }

    def _label(self, score: float) -> str:
        return "强势" if score >= 72 else "偏暖" if score >= 60 else "震荡" if score >= 45 else "偏弱" if score >= 35 else "弱势"
