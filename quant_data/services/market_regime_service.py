from __future__ import annotations
from quant_data.models import Quote

def _n(x, d=0.0):
    try: return float(x) if x is not None else d
    except Exception: return d

class MarketRegimeService:
    def analyze_quotes(self, quotes: list[Quote]) -> dict:
        if not quotes:
            return {"regime": "unknown", "score": 50, "basis": "无市场快照"}
        up = sum(1 for q in quotes if _n(q.change_pct) > 0)
        down = sum(1 for q in quotes if _n(q.change_pct) < 0)
        strong = sum(1 for q in quotes if _n(q.change_pct) >= 5)
        weak = sum(1 for q in quotes if _n(q.change_pct) <= -5)
        amount = sum(_n(q.amount) for q in quotes)
        up_ratio = up / max(1, up + down)
        score = 50 + (up_ratio - 0.5) * 60 + min(strong, 30) - min(weak, 30)
        regime = "牛市/强势" if score >= 70 else "震荡偏强" if score >= 58 else "震荡" if score >= 45 else "熊市/弱势"
        return {"regime": regime, "score": round(max(0, min(100, score)), 2), "up_count": up, "down_count": down, "up_ratio": round(up_ratio, 3), "strong_count": strong, "weak_count": weak, "sample_amount": amount, "basis": "基于当前快照涨跌家数、强弱家数和成交额估算市场体制。"}
