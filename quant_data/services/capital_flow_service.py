from __future__ import annotations
from quant_data.models import Quote, Bar


def _n(x, default=0.0):
    try: return float(x) if x is not None else default
    except Exception: return default


def _ma(vals, n):
    vals = [float(v) for v in vals if v is not None]
    return sum(vals[-n:]) / n if len(vals) >= n else None

class CapitalFlowService:
    def analyze(self, q: Quote, bars: list[Bar]) -> dict:
        amounts = [_n(b.amount) for b in bars]
        volumes = [_n(b.volume) for b in bars]
        closes = [_n(b.close) for b in bars]
        amt20 = _ma(amounts, 20)
        vol20 = _ma(volumes, 20)
        amount_strength = _n(q.amount) / amt20 if amt20 else None
        vol_strength = _n(q.volume) / vol20 if vol20 else None
        up_days = 0
        money_up_days = 0
        for i in range(max(1, len(closes)-5), len(closes)):
            if i > 0 and closes[i] >= closes[i-1]: up_days += 1
            if i > 0 and amounts[i] >= amounts[i-1]: money_up_days += 1
        score = 50
        tags = []
        risks = []
        if amount_strength is not None:
            if 1.2 <= amount_strength <= 3.5: score += 16; tags.append("成交额温和放大")
            elif amount_strength > 5: score -= 8; risks.append("成交额异常脉冲，一日游风险")
            elif amount_strength < 0.6: score -= 10; risks.append("成交额不足")
        if _n(q.volume_ratio) >= 1.3: score += 10; tags.append("量比资金关注")
        if money_up_days >= 3: score += 8; tags.append("近5日资金活跃延续")
        if _n(q.change_pct) > 0 and amount_strength and amount_strength < 0.9: risks.append("上涨但量能不足")
        if _n(q.change_pct) < -2 and amount_strength and amount_strength > 1.4: score -= 10; risks.append("放量下跌/资金分歧")
        level = "强" if score >= 75 else "中等" if score >= 55 else "弱"
        return {"capital_score": round(max(0, min(100, score)), 2), "capital_level": level, "amount_strength": round(amount_strength, 3) if amount_strength else None, "volume_strength": round(vol_strength, 3) if vol_strength else None, "recent_up_days": up_days, "recent_money_up_days": money_up_days, "tags": tags, "risks": risks, "basis": "基于公开行情的成交额、量比、成交量连续性估算；未伪造Level-2超大单。"}
