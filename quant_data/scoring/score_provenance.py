from __future__ import annotations

from hashlib import sha256
from math import isfinite
from typing import Any

from .score_models import FactorContribution, ScoreGate, ScoreProvenanceV323, ScoreRequest
from .score_policy import ScorePolicyV323


class ScoreProvenanceEngine:
    def __init__(self, policy: ScorePolicyV323 | None = None) -> None:
        self.policy = policy or ScorePolicyV323()

    def build(self, request: ScoreRequest | dict[str, Any]) -> ScoreProvenanceV323:
        req = request if isinstance(request, ScoreRequest) else ScoreRequest(**request)
        policy = self.policy
        contributions: list[FactorContribution] = []
        final = 0.0
        dimension_scores: dict[str, float] = {}
        valid_values: dict[str, float] = {}
        invalid_keys: list[str] = []
        for key, weight in policy.dimension_weights.items():
            value = req.factor_values.get(key)
            try:
                raw = float(value)
            except (TypeError, ValueError):
                raw = float("nan")
            if not isfinite(raw) or not 0.0 <= raw <= 100.0:
                invalid_keys.append(key)
                continue
            valid_values[key] = raw

        positive_weight = sum(
            max(0.0, policy.dimension_weights[key])
            for key in valid_values
            if policy.dimension_weights[key] >= 0
        )
        for key, raw in valid_values.items():
            weight = policy.dimension_weights[key]
            if weight >= 0:
                effective_weight = weight / positive_weight if positive_weight > 0 else 0.0
                contribution = raw * effective_weight
            else:
                effective_weight = weight
                contribution = -raw * abs(weight)
            final += contribution
            dimension_scores[key] = round(raw, 4)
            contributions.append(
                FactorContribution(
                    factor_key=key,
                    raw_value=round(raw, 4),
                    normalized_value=round(raw, 4),
                    weight=round(effective_weight, 6),
                    contribution=round(contribution, 6),
                    source=_source_for(req.data_sources, key),
                    source_time=_source_time(req.data_sources, key),
                    available_at=_available_at(req.data_sources, key, req.decision_time),
                    confidence=_confidence(req.data_sources, key),
                    explanation=_explain_dimension(key, raw, effective_weight),
                    dimension=key,
                )
            )
        gates = list(req.gates)
        missing = _missing(req.data_sources)
        excluded_dimensions = [
            {
                "factor_key": key,
                "raw_value": req.factor_values.get(key),
                "reason": "分值缺失、非有限数或超出0到100，未参与评分",
            }
            for key in invalid_keys
        ]
        stale = _stale(req.data_sources)
        if req.mode in {"realtime_paper", "live"} and stale and policy.stale_buy_block:
            gates.append(ScoreGate("stale_data_buy_block", False, "实时/实盘模式存在过期数据，禁止自动新增仓位", "block", penalty=20))
        if req.mode in {"realtime_paper", "live"}:
            quality = valid_values.get("data_quality_score")
            if quality is None:
                gates.append(
                    ScoreGate(
                        "data_quality_missing_block",
                        False,
                        "缺少可核验的数据质量分，禁止自动新增仓位",
                        "block",
                        penalty=0,
                    )
                )
            elif quality < policy.minimum_data_quality_for_new_position:
                gates.append(
                    ScoreGate(
                        "data_quality_low_block",
                        False,
                        f"数据质量 {quality:.1f} 低于门槛 {policy.minimum_data_quality_for_new_position:.1f}，禁止自动新增仓位",
                        "block",
                        penalty=0,
                    )
                )
        for gate in gates:
            if not gate.passed:
                final -= abs(gate.penalty)
        final = max(0.0, min(100.0, final)) if contributions else 0.0
        action = req.action_hint or ("buy" if final >= policy.buy_threshold else "sell" if final <= policy.sell_threshold else "hold")
        if any((not g.passed and g.severity == "block") for g in gates) and action in {"buy", "add"}:
            action = "hold"
        payload = f"{req.symbol}|{req.decision_time}|{req.mode}|{req.strategy_family}|{policy.policy_hash}|{round(final,4)}"
        return ScoreProvenanceV323(
            provenance_id="spv323-" + sha256(payload.encode("utf-8")).hexdigest()[:16],
            symbol=req.symbol,
            decision_time=req.decision_time,
            mode=req.mode,
            strategy_family=req.strategy_family,
            final_score=round(final, 4),
            action=action,
            factor_contributions=contributions,
            gates=gates,
            data_sources=list(req.data_sources),
            pit_status="point_in_time" if req.mode == "backtest" else "latest_snapshot",
            missing_data=list(dict.fromkeys(missing)),
            stale_data=list(dict.fromkeys(stale)),
            excluded_dimensions=excluded_dimensions,
            policy_version=policy.policy_version,
            policy_hash=policy.policy_hash,
            dimension_scores=dimension_scores,
        )


def build_score_provenance_v323(request: ScoreRequest | dict[str, Any], policy: ScorePolicyV323 | None = None) -> ScoreProvenanceV323:
    return ScoreProvenanceEngine(policy).build(request)


def _source_for(sources: list[dict[str, Any]], key: str) -> str:
    for src in sources:
        supports = src.get("supports") or src.get("fields") or []
        if key in supports or key.replace("_score", "") in supports:
            return str(src.get("source_id") or src.get("source_name") or "")
    return str((sources[0] or {}).get("source_id") or "") if sources else "数据源缺失"


def _source_time(sources: list[dict[str, Any]], key: str) -> str:
    for src in sources:
        if key in (src.get("supports") or src.get("fields") or []):
            return str(src.get("fetched_at") or src.get("published_at") or "")
    return str((sources[0] or {}).get("fetched_at") or "") if sources else ""


def _available_at(sources: list[dict[str, Any]], key: str, default: str) -> str:
    for src in sources:
        if key in (src.get("supports") or src.get("fields") or []):
            return str(src.get("available_at") or default)
    return str((sources[0] or {}).get("available_at") or default) if sources else default


def _confidence(sources: list[dict[str, Any]], key: str) -> float:
    if not sources:
        return 0.25
    stale = any(src.get("stale") for src in sources)
    missing = sum(len(src.get("missing_reasons") or []) for src in sources)
    return max(0.1, min(1.0, 0.92 - (0.22 if stale else 0.0) - missing * 0.03))


def _missing(sources: list[dict[str, Any]]) -> list[str]:
    rows: list[str] = []
    for src in sources:
        rows.extend(str(x) for x in (src.get("missing_reasons") or []))
    return rows


def _stale(sources: list[dict[str, Any]]) -> list[str]:
    return [str(src.get("source_name") or src.get("source_id") or "source") for src in sources if src.get("stale")]


def _explain_dimension(key: str, value: float, weight: float) -> str:
    labels = {
        "fundamental_score": "基本面质量、估值和财务增长",
        "technical_score": "K线趋势、均线、动量和波动",
        "information_score": "公告、新闻和重大事件",
        "fund_flow_score": "成交额、量比和公开资金流",
        "market_regime_score": "上证/创业板/宽基情绪与广度",
        "behavior_risk_score": "冲高回落、跌破均线、诱多等行为风险",
        "data_quality_score": "数据源新鲜度、缺失字段和可追溯性",
    }
    if key == "data_quality_score":
        return f"{labels[key]}：{value:.1f}，仅作为新鲜度与完整性门禁，不参与加权得分。"
    direction = "加分" if weight >= 0 else "风险扣分"
    return f"{labels.get(key, key)}：{value:.1f}，权重 {weight:.2f}，作为{direction}项。"
