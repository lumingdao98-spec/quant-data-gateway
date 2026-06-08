from __future__ import annotations

from typing import Any

from .score_models import ScoreProvenanceV323


def explain_score(provenance: ScoreProvenanceV323 | dict[str, Any]) -> dict[str, Any]:
    data = provenance.to_dict() if hasattr(provenance, "to_dict") else dict(provenance or {})
    contributions = data.get("factor_contributions") or []
    top = sorted(contributions, key=lambda x: abs(float(x.get("contribution") or 0)), reverse=True)[:5]
    blocks = [g for g in data.get("gates", []) if not g.get("passed")]
    return {
        "provenance_id": data.get("provenance_id"),
        "symbol": data.get("symbol"),
        "summary": f"最终评分 {data.get('final_score')}，动作 {data.get('action')}，策略族 {data.get('strategy_family')}",
        "top_contributors": top,
        "blocking_gates": blocks,
        "missing_data": data.get("missing_data") or [],
        "stale_data": data.get("stale_data") or [],
        "disclaimer": "研究辅助，不构成投资建议；真实交易需用户自行确认合规与风险。",
    }
