from __future__ import annotations
from quant_data.models import Quote

def _n(x, d=0.0):
    try: return float(x) if x is not None else d
    except Exception: return d

class ThemeLifecycleService:
    THEME_KEYWORDS = {
        "AI/算力": ["AI", "人工智能", "算力", "服务器", "光模块", "软件", "信创"],
        "半导体": ["半导体", "芯片", "晶圆", "EDA", "光刻", "集成电路"],
        "光伏": ["光伏", "硅料", "硅片", "组件", "太阳能"],
        "锂电/新能源车": ["锂", "电池", "新能源", "汽车", "储能"],
        "低空/军工": ["无人机", "航空", "航天", "军工", "低空"],
        "医药": ["医药", "药", "医疗", "生物"],
        "金融": ["银行", "证券", "保险", "金融"],
        "资源周期": ["煤", "钢", "有色", "黄金", "石油", "化工"],
    }
    def infer_themes(self, text: str) -> list[str]:
        text = text or ""
        out = []
        for theme, kws in self.THEME_KEYWORDS.items():
            if any(k.lower() in text.lower() for k in kws):
                out.append(theme)
        return out or ["未识别题材"]

    def analyze(self, q: Quote, evidence_text: str = "") -> dict:
        themes = self.infer_themes((q.name or "") + " " + evidence_text)
        chg = _n(q.change_pct); vr = _n(q.volume_ratio); to = _n(q.turnover)
        if chg >= 7 and vr >= 2:
            stage = "高潮/加速"
        elif chg >= 3 and vr >= 1.3:
            stage = "发酵"
        elif -2 <= chg <= 3 and vr >= 1.1:
            stage = "启动观察"
        elif chg < -3 and vr >= 1.5:
            stage = "分歧/退潮"
        else:
            stage = "低热度/待确认"
        score = 50 + min(max(chg, -10), 10) * 2 + min(vr, 5) * 5 + min(to, 20) * 0.8
        return {"themes": themes, "theme_stage": stage, "theme_score": round(max(0, min(100, score)), 2), "basis": "由公司名称/证据文本关键词、涨幅、量比、换手估算题材阶段；需结合板块成分股统计进一步确认。"}
