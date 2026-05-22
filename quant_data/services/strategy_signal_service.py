from __future__ import annotations
from quant_data.models import Quote, Bar
from quant_data.indicators import moving_average, rsi, bollinger, macd, atr

def _n(x, d=0.0):
    try: return float(x) if x is not None else d
    except Exception: return d

class StrategySignalService:
    def generate(self, q: Quote, bars: list[Bar], info_score: float | None = None) -> dict:
        closes=[_n(b.close) for b in bars]
        highs=[_n(b.high) for b in bars]; lows=[_n(b.low) for b in bars]
        last=_n(q.last or (closes[-1] if closes else 0))
        ma20=moving_average(closes,20); ma60=moving_average(closes,60)
        r=rsi(closes,14); b=bollinger(closes,20); m=macd(closes)
        dif=m.get('dif',[])[-1] if m.get('dif') else None; dea=m.get('dea',[])[-1] if m.get('dea') else None
        a=atr(highs,lows,closes,14) if len(closes)>=20 else None
        signals=[]
        def add(kind, strength, reason, horizon, risk):
            signals.append({"strategy":kind,"signal_strength":round(max(0,min(100,strength)),2),"entry_reason":reason,"holding_period":horizon,"risk_level":risk})
        if ma20 and ma60 and last>ma20>ma60: add("trend_following",70,"价格站上MA20且MA20在MA60之上","中短线","中")
        if r is not None and r<35 and b.get('lower') and last>=b.get('lower'): add("mean_reversion",65,"RSI偏低且接近/修复BOLL下轨","短线","中高")
        if dif is not None and dea is not None and dif>dea and _n(q.volume_ratio)>=1.2: add("momentum",68,"MACD多头且量比放大","短线/波段","中")
        if info_score is not None and info_score>=65 and _n(q.volume_ratio)>=1.1: add("event_driven",66,"信息面得分较高且量能有确认","事件周期","高")
        if a and last and a/last*100<5 and b.get('width_pct') and b.get('width_pct')<12: add("volatility_breakout_watch",58,"ATR和BOLL带宽收敛，等待方向选择","观察","中")
        if ma20 and abs(last/ma20-1)<0.03 and _n(q.volume_ratio)>=1.3: add("grid_or_swing",55,"价格贴近MA20且量能活跃，适合网格/波段观察","短线","中")
        if not signals: add("watch_only",45,"未形成可执行策略共振，仅保留观察","观察","中")
        return {"signals":signals,"best_signal":max(signals,key=lambda x:x['signal_strength']) if signals else None,"basis":"输出策略信号对象，供V4回测/V5模拟交易复用；当前不真实下单。"}
