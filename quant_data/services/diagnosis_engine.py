from __future__ import annotations
from quant_data.models import Quote

def _n(x, d=0.0):
    try: return float(x) if x is not None else d
    except Exception: return d

class DiagnosisEngine:
    def diagnose(self, q: Quote, base_score: float, scores: dict, tags: list[str], risks: list[str], evidence: dict | None = None) -> dict:
        evidence=evidence or {}
        score=float(base_score or 0)
        adjust=0.0; downgrade=[]; upgrade=[]; missing=[]
        if not evidence.get("has_policy") and any("政策" in t for t in tags):
            adjust-=8; downgrade.append("没有政策新闻证据，不能按政策驱动型加分")
        if risks:
            adjust-=min(15,len(risks)*3); downgrade.append("存在风险标签："+"、".join(risks[:4]))
        if scores.get("capital_score",0)>=70:
            adjust+=4; upgrade.append("资金活跃度有确认")
        if scores.get("theme_score",0)>=70:
            adjust+=3; upgrade.append("题材阶段偏活跃")
        if scores.get("technical_score",0)<55:
            adjust-=5; downgrade.append("技术面共振不足")
        if not evidence.get("has_industry"):
            missing.append("行业/板块证据不足")
        if not evidence.get("has_fundamental"):
            missing.append("基本面结构化数据不足")
        review_score=max(0,min(100,score+adjust))
        return {"script_score":round(score,2),"review_score":round(review_score,2),"score_adjustment":round(adjust,2),"upgrade_reasons":upgrade,"downgrade_reasons":downgrade,"missing_evidence":missing,"script_vs_manual":"脚本给出原始分；诊断引擎按证据完整性、资金确认和风险标签做复核建议，避免无证据硬判涨因。"}
