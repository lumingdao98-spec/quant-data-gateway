from __future__ import annotations

from typing import Any

from quant_data.factors.score_provenance import ScoreProvenance


def summarize_score_provenance(provenance: ScoreProvenance | dict[str, Any]) -> dict[str, Any]:
    data = provenance.to_dict() if hasattr(provenance, "to_dict") else dict(provenance or {})
    contributions = list(data.get("contributions") or [])
    positives = [x for x in contributions if float(x.get("contribution") or 0) > 0]
    negatives = [x for x in contributions if float(x.get("contribution") or 0) < 0]
    positives.sort(key=lambda x: float(x.get("contribution") or 0), reverse=True)
    negatives.sort(key=lambda x: float(x.get("contribution") or 0))
    return {
        "score_provenance_id": data.get("score_provenance_id"),
        "symbol": data.get("symbol"),
        "final_score": data.get("final_score"),
        "strategy_family": data.get("strategy_family"),
        "coverage_pct": data.get("coverage_pct"),
        "no_lookahead": data.get("no_lookahead"),
        "top_positive": [
            {"factor_key": x.get("factor_key"), "contribution": x.get("contribution"), "source_refs": x.get("source_refs", [])}
            for x in positives[:5]
        ],
        "top_negative": [
            {"factor_key": x.get("factor_key"), "contribution": x.get("contribution"), "source_refs": x.get("source_refs", [])}
            for x in negatives[:5]
        ],
        "gate_warnings": [g.get("reason") for g in data.get("gates", []) if not g.get("passed") and g.get("reason")],
        "warnings": data.get("warnings", []),
    }


def summarize_many(items: list[ScoreProvenance | dict[str, Any]], *, limit: int = 20) -> list[dict[str, Any]]:
    return [summarize_score_provenance(x) for x in items[: max(1, int(limit or 20))]]
