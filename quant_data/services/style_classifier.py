from __future__ import annotations
from quant_data.models import Quote, Bar, AssetType

def _n(x, d=0.0):
    try: return float(x) if x is not None else d
    except Exception: return d

class StyleClassifierService:
    def classify(self, q: Quote, bars: list[Bar] | None = None) -> dict:
        cap = _n(q.float_market_cap or q.total_market_cap)
        cap_yi = cap / 100_000_000 if cap else None
        labels = []
        if q.asset_type == AssetType.ETF:
            labels.append("ETF")
        if cap_yi is not None:
            if cap_yi < 50: labels.append("微小盘")
            elif cap_yi < 100: labels.append("小盘")
            elif cap_yi < 500: labels.append("中盘")
            elif cap_yi < 2000: labels.append("大盘")
            else: labels.append("超大盘")
        if _n(q.turnover) >= 8: labels.append("高换手弹性")
        if _n(q.volume_ratio) >= 2: labels.append("量能活跃")
        if q.pe_dynamic is not None and 0 < _n(q.pe_dynamic) < 20: labels.append("低估值")
        if q.pb is not None and 0 < _n(q.pb) < 1.5: labels.append("低PB")
        if q.pe_dynamic is not None and _n(q.pe_dynamic) > 80: labels.append("高估值成长/题材")
        name = q.name or ""
        if any(k in name for k in ["银行", "煤", "电力", "石化", "高速"]): labels.append("高股息/周期防御观察")
        if any(k in name.upper() for k in ["ST", "退"]): labels.append("风险股")
        logic = ""
        if "小盘" in labels or "微小盘" in labels:
            logic = "小盘股更看题材、换手、控盘和风险，不能只按基本面打分。"
        elif "大盘" in labels or "超大盘" in labels:
            logic = "大盘股更受指数环境、机构资金和估值约束影响。"
        elif "ETF" in labels:
            logic = "ETF按基金画像、流动性、跟踪指数和折溢价分析，不按上市公司处理。"
        else:
            logic = "中盘股需兼顾业绩、行业地位和资金持续性。"
        return {"style_labels": list(dict.fromkeys(labels)), "float_cap_yi": round(cap_yi, 2) if cap_yi else None, "style_logic": logic}
