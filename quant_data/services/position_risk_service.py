from __future__ import annotations
from quant_data.models import Quote, Bar
from quant_data.indicators import atr, support_resistance

def _n(x, d=0.0):
    try: return float(x) if x is not None else d
    except Exception: return d

class PositionRiskService:
    def analyze(self, q: Quote, bars: list[Bar], risk_flags: list[str] | None = None) -> dict:
        highs=[_n(b.high) for b in bars]; lows=[_n(b.low) for b in bars]; closes=[_n(b.close) for b in bars]
        last=_n(q.last or (closes[-1] if closes else 0))
        a=atr(highs,lows,closes,14) if len(bars)>=20 else None
        sr=support_resistance(highs,lows,closes,60) if len(bars)>=60 else {}
        support=sr.get("support")
        stop_candidates=[]
        if a and last: stop_candidates.append(last-2*a)
        if support: stop_candidates.append(float(support)*0.985)
        stop=max([x for x in stop_candidates if x and x>0], default=None)
        risk_count=len(risk_flags or [])
        if risk_count>=4 or _n(q.change_pct)>8 or (a and last and a/last*100>8):
            action="禁入/只观察"
            max_pos=0
        elif risk_count>=2:
            action="轻仓观察"
            max_pos=5
        elif _n(q.volume_ratio)>=1.3 and -3<=_n(q.change_pct)<=6:
            action="观察确认后小仓试错"
            max_pos=10
        else:
            action="正常观察"
            max_pos=8
        return {"risk_action": action, "max_single_position_pct": max_pos, "atr14": round(a,4) if a else None, "stop_loss_ref": round(stop,4) if stop else None, "support_ref": round(support,4) if support else None, "risk_flags_count": risk_count, "basis": "V3.x只给模拟风控建议，不自动下单。止损参考取2ATR和支撑位下沿。"}
