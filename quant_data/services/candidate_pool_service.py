from __future__ import annotations
from dataclasses import dataclass, asdict
from quant_data.models import Quote

@dataclass
class CandidateMeta:
    symbol: str
    name: str
    channels: list[str]
    reason: str
    rank_score: float


def _n(x, default=0.0):
    try:
        return float(x) if x is not None else default
    except Exception:
        return default


class CandidatePoolService:
    """三通道候选池：换手率TOP50、成交额TOP20、技术初筛。

    这一步只负责“圈值得看的票”，不直接给最终买卖结论。
    """

    def is_valid_quote(self, q: Quote, min_amount: float = 10_000_000) -> bool:
        name = (q.name or "").upper()
        if any(k in name for k in ["ST", "*ST", "退"]):
            return False
        if _n(q.last) <= 0:
            return False
        if _n(q.amount) < min_amount:
            return False
        return True

    def build(self, quotes: list[Quote], max_items: int = 120) -> dict:
        pool = [q for q in quotes if self.is_valid_quote(q)]
        turnover_top = sorted(pool, key=lambda q: _n(q.turnover), reverse=True)[:50]
        amount_top = sorted(pool, key=lambda q: _n(q.amount), reverse=True)[:20]
        tech_seed = [q for q in pool if _n(q.volume_ratio) >= 1.3 and -4.5 <= _n(q.change_pct) <= 8.5]
        tech_seed = sorted(tech_seed, key=lambda q: (_n(q.volume_ratio), _n(q.amount)), reverse=True)[:100]
        channel_map: dict[str, set[str]] = {}
        obj: dict[str, Quote] = {}
        for label, block in [("turnover_top50", turnover_top), ("amount_top20", amount_top), ("technical_seed", tech_seed)]:
            for q in block:
                obj[q.symbol] = q
                channel_map.setdefault(q.symbol, set()).add(label)
        scored: list[tuple[float, Quote]] = []
        for q in obj.values():
            score = len(channel_map.get(q.symbol, [])) * 30 + min(_n(q.volume_ratio) * 8, 30) + min(_n(q.turnover), 20) + min(_n(q.amount) / 100_000_000, 20)
            scored.append((score, q))
        scored.sort(key=lambda x: x[0], reverse=True)
        selected = scored[: max(1, int(max_items or 120))]
        metas = []
        for score, q in selected:
            chs = sorted(channel_map.get(q.symbol, []))
            reasons = []
            if "turnover_top50" in chs: reasons.append("换手率活跃")
            if "amount_top20" in chs: reasons.append("成交额靠前")
            if "technical_seed" in chs: reasons.append("量比/涨幅处于技术初筛区间")
            metas.append(asdict(CandidateMeta(q.symbol, q.name, chs, "；".join(reasons), round(score, 2))))
        return {
            "candidate_count": len(selected),
            "raw_quote_count": len(quotes),
            "valid_quote_count": len(pool),
            "rules": {
                "channel1": "换手率TOP50，捕捉资金活跃票",
                "channel2": "成交额TOP20，防止只按换手遗漏大票",
                "channel3": "技术初筛：量比>=1.3且非极端追高/杀跌",
                "dedup": "三通道按symbol去重，并保留通道标签",
            },
            "candidates": metas,
            "selected_symbols": [q.symbol for _, q in selected],
        }
