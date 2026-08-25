from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any

from quant_data.strategy.strategy_family import normalize_strategy_family

from .execution_policy import EXECUTION_SCORE_THRESHOLDS, EXECUTION_SCORE_WEIGHTS


ADAPTIVE_POLICY_VERSION = "v3.28-regime-bounded"


STRATEGY_WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    "short": {
        "fundamental": 0.06,
        "technical": 0.36,
        "information": 0.22,
        "fund_flow": 0.24,
        "market": 0.12,
    },
    "swing": dict(EXECUTION_SCORE_WEIGHTS),
    "position": {
        "fundamental": 0.34,
        "technical": 0.22,
        "information": 0.18,
        "fund_flow": 0.10,
        "market": 0.16,
    },
    "core_satellite": {
        "fundamental": 0.28,
        "technical": 0.25,
        "information": 0.18,
        "fund_flow": 0.13,
        "market": 0.16,
    },
    "dca": {
        "fundamental": 0.00,
        "technical": 0.38,
        "information": 0.12,
        "fund_flow": 0.26,
        "market": 0.24,
    },
    "event_driven": {
        "fundamental": 0.12,
        "technical": 0.24,
        "information": 0.36,
        "fund_flow": 0.14,
        "market": 0.14,
    },
    "avoid": dict(EXECUTION_SCORE_WEIGHTS),
}


STRATEGY_LABELS = {
    "short": "短线/盘中",
    "swing": "波段",
    "position": "中长线",
    "core_satellite": "核心-卫星",
    "dca": "ETF/定投",
    "event_driven": "事件驱动",
    "avoid": "规避观察",
}


@dataclass(frozen=True, slots=True)
class AdaptiveExecutionDecision:
    policy_version: str
    strategy_family: str
    strategy_label: str
    market_band: str
    weight_mode: str
    weights: dict[str, float]
    thresholds: dict[str, float]
    position_scale: float
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AdaptiveExecutionPolicy:
    """Resolve bounded strategy/regime adjustments for the execution score.

    The resolver never manufactures a missing factor. It only chooses the
    configured weight of factors that later pass the normal readiness checks.
    Explicit manual weights remain supported and always win over profiles.
    """

    _ALIASES = {
        "screening": ("screening", "screening_score", "screener", "screener_score"),
        "fundamental": ("fundamental", "fundamental_score"),
        "technical": ("technical", "technical_score"),
        "information": ("information", "information_score", "info"),
        "fund_flow": ("fund_flow", "fund_flow_score", "capital", "money"),
        "market": ("market", "market_regime", "market_score"),
    }

    def resolve(
        self,
        *,
        strategy_family: str | None = None,
        horizon: str | None = None,
        market_score: Any = None,
        score_weights: dict[str, Any] | None = None,
        base_thresholds: dict[str, float] | None = None,
        weak_market_cut: float = 0.65,
    ) -> AdaptiveExecutionDecision:
        family = normalize_strategy_family(strategy_family or horizon or "swing", default="swing")
        manual = self._manual_weights(score_weights)
        weights = manual or dict(STRATEGY_WEIGHT_PROFILES.get(family, STRATEGY_WEIGHT_PROFILES["swing"]))
        weight_mode = "manual" if manual else "adaptive"
        rationale = [
            "用户手工权重优先，系统只对有效维度重新归一化"
            if manual
            else f"采用{STRATEGY_LABELS.get(family, '波段')}策略权重模板"
        ]

        thresholds = {
            "buy": float((base_thresholds or {}).get("buy", EXECUTION_SCORE_THRESHOLDS["buy"])),
            "add": float((base_thresholds or {}).get("add", EXECUTION_SCORE_THRESHOLDS["add"])),
            "reduce_or_sell": float(
                (base_thresholds or {}).get("reduce_or_sell", EXECUTION_SCORE_THRESHOLDS["reduce_or_sell"])
            ),
        }
        position_scale = 1.0
        market_value = self._score(market_score)
        if market_value is None:
            market_band = "证据不足"
            position_scale = min(0.75, max(0.0, float(weak_market_cut)))
            thresholds["buy"] += 2.0
            thresholds["add"] += 2.0
            rationale.append("大盘环境缺少有效证据：不补中性分，提高入场阈值并降低目标仓位")
        elif market_value <= 35.0:
            market_band = "弱势"
            position_scale = min(0.60, max(0.0, float(weak_market_cut)))
            thresholds["buy"] += 4.0
            thresholds["add"] += 4.0
            if not manual:
                weights = self._shift_for_weak_market(weights)
            rationale.append("大盘弱势：买入/加仓阈值提高4分，目标仓位最多保留60%")
        elif market_value >= 70.0:
            market_band = "强势"
            thresholds["buy"] -= 1.0
            thresholds["add"] -= 1.0
            rationale.append("大盘强势：入场阈值仅放宽1分，不放大仓位上限")
        else:
            market_band = "中性"
            rationale.append("大盘中性：不额外调整阈值或仓位")

        if family == "avoid":
            thresholds["buy"] = 100.0
            thresholds["add"] = 100.0
            position_scale = 0.0
            rationale.append("规避策略禁止自动新增仓位")

        weights = self._normalize(weights)
        return AdaptiveExecutionDecision(
            policy_version=ADAPTIVE_POLICY_VERSION,
            strategy_family=family,
            strategy_label=STRATEGY_LABELS.get(family, family),
            market_band=market_band,
            weight_mode=weight_mode,
            weights=weights,
            thresholds={key: round(value, 4) for key, value in thresholds.items()},
            position_scale=round(position_scale, 4),
            rationale=rationale,
        )

    def _manual_weights(self, values: dict[str, Any] | None) -> dict[str, float]:
        if not isinstance(values, dict):
            return {}
        mode = str(values.get("mode") or values.get("weight_mode") or "manual").strip().lower()
        if mode in {"adaptive", "auto", "strategy"} and not bool(values.get("manual")):
            return {}
        out: dict[str, float] = {}
        for key, aliases in self._ALIASES.items():
            if key == "screening":
                continue
            for alias in aliases:
                parsed = self._positive(values.get(alias))
                if parsed is not None:
                    out[key] = parsed
                    break
        return out if out else {}

    @staticmethod
    def _shift_for_weak_market(weights: dict[str, float]) -> dict[str, float]:
        shifted = dict(weights)
        deltas = {
            "fundamental": -0.02,
            "technical": 0.01,
            "information": -0.02,
            "fund_flow": 0.01,
            "market": 0.02,
        }
        for key, delta in deltas.items():
            shifted[key] = max(0.0, float(shifted.get(key, 0.0)) + delta)
        return shifted

    @staticmethod
    def _normalize(weights: dict[str, float]) -> dict[str, float]:
        keys = ("fundamental", "technical", "information", "fund_flow", "market")
        total = sum(max(0.0, float(weights.get(key, 0.0))) for key in keys)
        if total <= 0:
            return dict(EXECUTION_SCORE_WEIGHTS)
        return {key: round(max(0.0, float(weights.get(key, 0.0))) / total, 8) for key in keys}

    @staticmethod
    def _positive(value: Any) -> float | None:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        return parsed if isfinite(parsed) and parsed > 0 else None

    @staticmethod
    def _score(value: Any) -> float | None:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        return parsed if isfinite(parsed) and 0.0 <= parsed <= 100.0 else None
