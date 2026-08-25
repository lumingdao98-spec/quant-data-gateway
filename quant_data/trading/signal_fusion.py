from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from math import isfinite
from typing import Any, Literal

from quant_data.scoring.adaptive_execution_policy import AdaptiveExecutionPolicy
from quant_data.scoring.execution_policy import EXECUTION_SCORE_THRESHOLDS, EXECUTION_SCORE_WEIGHTS


SignalAction = Literal["buy", "sell", "hold", "reduce", "add", "avoid"]


@dataclass(slots=True)
class UnifiedSignal:
    symbol: str
    timestamp: str
    horizon: str
    action: SignalAction
    confidence: float
    final_score: float
    screening_score: float | None = None
    daily_k_score: float | None = None
    intraday_score: float | None = None
    fundamental_score: float | None = None
    technical_score: float | None = None
    information_score: float | None = None
    fund_flow_score: float | None = None
    market_score: float | None = None
    anomaly_score: float = 0.0
    risk_level: str = "medium"
    target_weight: float = 0.0
    max_risk_pct: float = 0.02
    reason: str = ""
    evidence: list[str] = field(default_factory=list)
    data_freshness: dict[str, Any] = field(default_factory=dict)
    missing_data: list[str] = field(default_factory=list)
    requires_manual_confirm: bool = False
    score_breakdown: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SignalFusionConfig:
    # The screener total already contains several dimensions below. It is an
    # audit prior, not another vote, otherwise technical/information/fund flow
    # would be counted twice. It is used only when every component is missing.
    screening_weight: float = 0.0
    fundamental_weight: float = EXECUTION_SCORE_WEIGHTS["fundamental"]
    technical_weight: float = EXECUTION_SCORE_WEIGHTS["technical"]
    information_weight: float = EXECUTION_SCORE_WEIGHTS["information"]
    fund_flow_weight: float = EXECUTION_SCORE_WEIGHTS["fund_flow"]
    market_weight: float = EXECUTION_SCORE_WEIGHTS["market"]
    buy_threshold: float = EXECUTION_SCORE_THRESHOLDS["buy"]
    sell_threshold: float = EXECUTION_SCORE_THRESHOLDS["reduce_or_sell"]
    add_threshold: float = EXECUTION_SCORE_THRESHOLDS["add"]
    max_target_weight: float = 0.25
    weak_market_cut: float = 0.65


class SignalFusionEngine:
    def __init__(self, config: SignalFusionConfig | None = None) -> None:
        self.config = config or SignalFusionConfig()
        self.adaptive_policy = AdaptiveExecutionPolicy()

    def fuse(
        self,
        *,
        symbol: str,
        horizon: str = "swing",
        screening_score: float | None = None,
        daily_k_score: float | None = None,
        intraday_score: float | None = None,
        fundamental_score: float | None = None,
        technical_score: float | None = None,
        information_score: float | None = None,
        fund_flow_score: float | None = None,
        market_score: float | None = None,
        score_weights: dict[str, Any] | None = None,
        anomaly_score: float = 0.0,
        evidence: list[str] | None = None,
        data_freshness: dict[str, Any] | None = None,
        missing_data: list[str] | None = None,
        info_negative_veto: bool = False,
        anomaly_action: str | None = None,
        technical_broken: bool = False,
        fundamental_poor: bool = False,
        strategy_family: str | None = None,
        now: datetime | None = None,
    ) -> UnifiedSignal:
        cfg = self.config
        raw_scores = {
            "screening": screening_score,
            "fundamental": fundamental_score,
            "technical": technical_score,
            "information": information_score,
            "fund_flow": fund_flow_score,
            "market": market_score,
        }
        adaptive = self.adaptive_policy.resolve(
            strategy_family=strategy_family,
            horizon=horizon,
            market_score=market_score,
            score_weights=score_weights,
            base_thresholds={
                "buy": cfg.buy_threshold,
                "add": cfg.add_threshold,
                "reduce_or_sell": cfg.sell_threshold,
            },
            weak_market_cut=cfg.weak_market_cut,
        )
        weights = {"screening": cfg.screening_weight, **adaptive.weights}
        scores: dict[str, float | None] = {}
        invalid_dimensions: list[dict[str, Any]] = []
        for key, value in raw_scores.items():
            if value is None:
                scores[key] = None
                continue
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                parsed = float("nan")
            if not isfinite(parsed) or not 0.0 <= parsed <= 100.0:
                scores[key] = None
                invalid_dimensions.append({"key": key, "value": value, "reason": "分值必须是0到100之间的有限数"})
            else:
                scores[key] = parsed

        invalid_risk_inputs: list[dict[str, Any]] = []
        try:
            anomaly_value = float(anomaly_score or 0.0)
        except (TypeError, ValueError):
            anomaly_value = float("nan")
        if not isfinite(anomaly_value) or anomaly_value < 0.0:
            invalid_risk_inputs.append({"key": "anomaly_score", "value": anomaly_score, "reason": "异常分无效，按高风险处理"})
            anomaly_value = 80.0
        anomaly_score = min(anomaly_value, 100.0)

        component_keys = ("fundamental", "technical", "information", "fund_flow", "market")
        component_usable = {key: scores[key] for key in component_keys if scores[key] is not None}
        screening_fallback = not component_usable and scores["screening"] is not None
        usable = component_usable or ({"screening": scores["screening"]} if screening_fallback else {})
        # screening_score remains in the provenance for comparison, but is not
        # allowed to double count its own component scores.
        audit_only_dimensions = ["screening"] if scores["screening"] is not None and not screening_fallback else []
        missing = list(missing_data or []) + [key for key in component_keys if scores[key] is None]
        missing.extend(f"invalid_{row['key']}_score" for row in invalid_dimensions)
        total_w = sum(max(0.0, weights[k]) for k in usable)
        if usable and total_w <= 0:
            total_w = float(len(usable))
            effective_weights = {key: 1.0 for key in usable}
        else:
            effective_weights = {key: max(0.0, weights[key]) for key in usable}
        contributions = []
        labels = {
            "screening": "筛选底座",
            "fundamental": "基本面",
            "technical": "实时择时",
            "information": "近期信息",
            "fund_flow": "量价资金",
            "market": "大盘环境",
        }
        for key, value in usable.items():
            normalized_weight = effective_weights[key] / (total_w or 1.0)
            contributions.append(
                {
                    "key": key,
                    "label": labels[key],
                    "score": round(float(value), 4),
                    "configured_weight": round(weights[key], 6),
                    "normalized_weight": round(normalized_weight, 6),
                    "contribution": round(float(value) * normalized_weight, 4),
                }
            )
        score_before_risk = sum(float(row["contribution"]) for row in contributions)
        anomaly_deduction = min(float(anomaly_score or 0.0) * 0.35, 35.0)
        final_score = score_before_risk - anomaly_deduction
        final_score = max(0.0, min(100.0, final_score))
        score_breakdown = {
            "formula": "综合交易分 = 基本面/实时技术/近期信息/资金面/大盘环境按有效权重归一化 - 异常风险扣分；筛选总分只作审计底座，不重复计票",
            "timing_formula": "实时择时分 = 日K结构55% + 当日分时45%",
            "contributions": contributions,
            "available_weight_total": round(total_w if usable else 0.0, 6),
            "normalized_weight_total": round(sum(effective_weights[key] / (total_w or 1.0) for key in usable), 6),
            "score_before_risk": round(score_before_risk, 4),
            "anomaly_score": round(float(anomaly_score or 0.0), 4),
            "anomaly_deduction": round(anomaly_deduction, 4),
            "final_score": round(final_score, 4),
            "missing_dimensions": [labels[key] for key in component_keys if scores[key] is None],
            "invalid_dimensions": invalid_dimensions,
            "invalid_risk_inputs": invalid_risk_inputs,
            "audit_only_dimensions": [labels[key] for key in audit_only_dimensions],
            "screening_score_audit": scores.get("screening"),
            "screening_fallback_used": screening_fallback,
            "weight_policy": "缺失或无效分项不参与；剩余有效分项重新归一化到100%。筛选总分仅在所有分项都缺失时作低置信兜底。",
            "configured_weights": {key: round(float(weights[key]), 6) for key in component_keys},
            "thresholds": {
                **adaptive.thresholds,
            },
            "adaptive_policy": adaptive.to_dict(),
        }
        action: SignalAction = "hold"
        reason_parts: list[str] = []
        if info_negative_veto:
            action = "avoid"
            reason_parts.append("信息面重大负面 veto 买入")
        elif anomaly_action in {"block_buy", "force_exit"}:
            action = "reduce" if anomaly_action == "force_exit" else "avoid"
            reason_parts.append("异常波动触发规避")
        elif final_score >= adaptive.thresholds["add"] and anomaly_score < 25:
            action = "add"
            reason_parts.append("综合评分强且异常较低")
        elif final_score >= adaptive.thresholds["buy"] and anomaly_score < 35:
            action = "buy"
            reason_parts.append("综合评分达到买入观察阈值")
        elif final_score <= adaptive.thresholds["reduce_or_sell"] or anomaly_score >= 55:
            action = "sell" if anomaly_score >= 55 else "reduce"
            reason_parts.append("评分转弱或异常升高")
        else:
            reason_parts.append("评分处于观察区间")
        if fundamental_poor and technical_score is not None and technical_score >= 70:
            reason_parts.append("基本面长期偏弱，仅允许短线小仓")
        if technical_broken and (fundamental_score or 0) >= 65:
            action = "hold" if action in {"buy", "add"} else action
            reason_parts.append("基本面较好但技术破位，禁止短线追买")
        market_scale = adaptive.position_scale
        if market_scale < 1:
            reason_parts.append("大盘弱势降低目标仓位")
        base_weight = cfg.max_target_weight * max(0.0, (final_score - 45.0) / 55.0) * market_scale
        if fundamental_poor and horizon in {"short_term", "intraday_paper"}:
            base_weight = min(base_weight, cfg.max_target_weight * 0.35)
        if action in {"avoid", "sell"}:
            base_weight = 0.0
        elif action == "reduce":
            base_weight = min(base_weight, cfg.max_target_weight * 0.35)
        coverage = len(component_usable) / float(len(component_keys))
        confidence = min(1.0, max(0.0, coverage * (1.0 - min(anomaly_score, 80) / 120.0)))
        if screening_fallback:
            confidence = min(confidence or 0.25, 0.25)
        risk_level = "low" if anomaly_score < 20 and final_score >= 65 else "high" if anomaly_score >= 45 or final_score < 45 else "medium"
        freshness = data_freshness or {}
        requires_confirm = bool(missing or freshness.get("action") in {"reduce", "refresh_required"} or anomaly_action == "manual_confirm")
        return UnifiedSignal(
            symbol=symbol,
            timestamp=(now or datetime.now()).isoformat(timespec="seconds"),
            horizon=horizon,
            action=action,
            confidence=round(confidence, 4),
            final_score=round(final_score, 2),
            screening_score=screening_score,
            daily_k_score=daily_k_score,
            intraday_score=intraday_score,
            fundamental_score=fundamental_score,
            technical_score=technical_score,
            information_score=information_score,
            fund_flow_score=fund_flow_score,
            market_score=market_score,
            anomaly_score=round(float(anomaly_score or 0.0), 2),
            risk_level=risk_level,
            target_weight=round(max(0.0, min(cfg.max_target_weight, base_weight)), 6),
            max_risk_pct=0.01 if risk_level == "high" else 0.02,
            reason="；".join(reason_parts),
            evidence=list(evidence or []),
            data_freshness=freshness,
            missing_data=list(dict.fromkeys(missing)),
            requires_manual_confirm=requires_confirm,
            score_breakdown=score_breakdown,
        )
