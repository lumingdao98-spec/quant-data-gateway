from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Literal


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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SignalFusionConfig:
    screening_weight: float = 0.30
    fundamental_weight: float = 0.28
    technical_weight: float = 0.34
    information_weight: float = 0.24
    fund_flow_weight: float = 0.16
    market_weight: float = 0.14
    buy_threshold: float = 62.0
    sell_threshold: float = 45.0
    add_threshold: float = 72.0
    max_target_weight: float = 0.25
    weak_market_cut: float = 0.65


class SignalFusionEngine:
    def __init__(self, config: SignalFusionConfig | None = None) -> None:
        self.config = config or SignalFusionConfig()

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
        now: datetime | None = None,
    ) -> UnifiedSignal:
        cfg = self.config
        scores = {
            "screening": screening_score,
            "fundamental": fundamental_score,
            "technical": technical_score,
            "information": information_score,
            "fund_flow": fund_flow_score,
            "market": market_score,
        }
        weights = {
            "screening": cfg.screening_weight,
            "fundamental": cfg.fundamental_weight,
            "technical": cfg.technical_weight,
            "information": cfg.information_weight,
            "fund_flow": cfg.fund_flow_weight,
            "market": cfg.market_weight,
        }
        if score_weights:
            aliases = {
                "screening": ("screening", "screening_score", "screener", "screener_score"),
                "fundamental": ("fundamental", "fundamental_score"),
                "technical": ("technical", "technical_score"),
                "information": ("information", "information_score", "info"),
                "fund_flow": ("fund_flow", "fund_flow_score", "capital", "money"),
                "market": ("market", "market_regime", "market_score"),
            }
            for key, names in aliases.items():
                for name in names:
                    if name not in score_weights:
                        continue
                    try:
                        value = float(score_weights[name])
                    except (TypeError, ValueError):
                        continue
                    if value > 0:
                        weights[key] = value
                    break
        usable = {k: v for k, v in scores.items() if v is not None}
        # screening_score is a V3.23 baseline. Older callers remain valid and
        # are not marked incomplete only because they do not provide it.
        missing = list(missing_data or []) + [k for k in scores if k != "screening" and scores[k] is None]
        if usable:
            total_w = sum(weights[k] for k in usable) or 1.0
            final_score = sum(float(usable[k]) * weights[k] / total_w for k in usable)
        else:
            final_score = 0.0
        final_score -= min(float(anomaly_score or 0.0) * 0.35, 35.0)
        final_score = max(0.0, min(100.0, final_score))
        action: SignalAction = "hold"
        reason_parts: list[str] = []
        if info_negative_veto:
            action = "avoid"
            reason_parts.append("信息面重大负面 veto 买入")
        elif anomaly_action in {"block_buy", "force_exit"}:
            action = "reduce" if anomaly_action == "force_exit" else "avoid"
            reason_parts.append("异常波动触发规避")
        elif final_score >= cfg.add_threshold and anomaly_score < 25:
            action = "add"
            reason_parts.append("综合评分强且异常较低")
        elif final_score >= cfg.buy_threshold and anomaly_score < 35:
            action = "buy"
            reason_parts.append("综合评分达到买入观察阈值")
        elif final_score <= cfg.sell_threshold or anomaly_score >= 55:
            action = "sell" if anomaly_score >= 55 else "reduce"
            reason_parts.append("评分转弱或异常升高")
        else:
            reason_parts.append("评分处于观察区间")
        if fundamental_poor and technical_score is not None and technical_score >= 70:
            reason_parts.append("基本面长期偏弱，仅允许短线小仓")
        if technical_broken and (fundamental_score or 0) >= 65:
            action = "hold" if action in {"buy", "add"} else action
            reason_parts.append("基本面较好但技术破位，禁止短线追买")
        market_scale = cfg.weak_market_cut if market_score is not None and market_score < 40 else 1.0
        if market_scale < 1:
            reason_parts.append("大盘弱势降低目标仓位")
        base_weight = cfg.max_target_weight * max(0.0, (final_score - 45.0) / 55.0) * market_scale
        if fundamental_poor and horizon in {"short_term", "intraday_paper"}:
            base_weight = min(base_weight, cfg.max_target_weight * 0.35)
        if action in {"avoid", "sell"}:
            base_weight = 0.0
        elif action == "reduce":
            base_weight = min(base_weight, cfg.max_target_weight * 0.35)
        expected_dims = (5.0 if fund_flow_score is not None else 4.0) + (1.0 if screening_score is not None else 0.0)
        confidence = min(1.0, max(0.0, len(usable) / expected_dims * (1.0 - min(anomaly_score, 80) / 120.0)))
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
        )
