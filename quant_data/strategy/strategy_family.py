from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any


CANONICAL_STRATEGY_FAMILIES = (
    "short",
    "swing",
    "position",
    "dca",
    "core_satellite",
    "event_driven",
    "avoid",
)

STRATEGY_FAMILY_ALIASES = {
    "short": "short",
    "short_term": "short",
    "short_term_momentum": "short",
    "intraday": "short",
    "swing": "swing",
    "position": "position",
    "long_term": "position",
    "long": "position",
    "dca": "dca",
    "core_satellite": "core_satellite",
    "hybrid": "core_satellite",
    "event_driven": "event_driven",
    "event": "event_driven",
    "avoid": "avoid",
    "watch": "avoid",
}


def normalize_strategy_family(value: Any, *, default: str = "core_satellite") -> str:
    key = str(value or "").strip().lower().replace("-", "_")
    normalized = STRATEGY_FAMILY_ALIASES.get(key, key)
    return normalized if normalized in CANONICAL_STRATEGY_FAMILIES else default


@dataclass(frozen=True, slots=True)
class StrategyExecutionProfile:
    strategy_family: str
    name: str
    horizon: str
    entry_score_threshold: float
    sizing_model: str
    add_rule: str
    exit_policy: str
    stop_loss_pct: float | None
    take_profit_pct: float | None
    trailing_stop_pct: float | None
    max_position_pct: float
    event_expiry_minutes: int = 0
    dca_interval_days: int = 0
    profile_version: str = "v3.24.0"

    @property
    def profile_hash(self) -> str:
        payload = json.dumps(asdict(self), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()[:24]

    @property
    def policy_hash(self) -> str:
        payload = {
            "family": self.strategy_family,
            "entry": self.entry_score_threshold,
            "sizing": self.sizing_model,
            "add_rule": self.add_rule,
            "exit": self.exit_policy,
            "stop": self.stop_loss_pct,
            "take": self.take_profit_pct,
            "trail": self.trailing_stop_pct,
            "max_position": self.max_position_pct,
            "event_expiry": self.event_expiry_minutes,
            "dca_interval": self.dca_interval_days,
            "version": self.profile_version,
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return sha256(raw.encode("utf-8")).hexdigest()[:24]

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "profile_hash": self.profile_hash, "policy_hash": self.policy_hash}


@dataclass(frozen=True, slots=True)
class StrategyFamily:
    key: str
    name: str
    horizon: str
    default_sizing: str
    default_exit: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


STRATEGY_EXECUTION_PROFILES = {
    "short": StrategyExecutionProfile(
        "short", "短线", "盘中至数日", 68.0, "score_weighted", "不追高，确认后一次加仓",
        "quick_stop_take_profit", 0.045, 0.09, 0.035, 0.12,
    ),
    "swing": StrategyExecutionProfile(
        "swing", "波段", "数日至数周", 62.0, "atr_risk", "趋势延续且回踩不破时分批加仓",
        "atr_trailing_stop", 0.08, 0.18, 0.08, 0.20,
    ),
    "position": StrategyExecutionProfile(
        "position", "中长线持仓", "数月至更长", 64.0, "volatility_target", "基本面与长期趋势同时改善时分批加仓",
        "thesis_break_exit", None, None, 0.15, 0.30,
    ),
    "dca": StrategyExecutionProfile(
        "dca", "定投", "固定周期", 50.0, "dca_schedule", "按计划执行，低估时提高当期额度",
        "market_emergency_exit", None, None, None, 0.25, dca_interval_days=20,
    ),
    "core_satellite": StrategyExecutionProfile(
        "core_satellite", "核心-卫星", "长期核心与短期增强", 60.0, "core_satellite", "核心仓与卫星仓分别核算并分批调整",
        "staged_take_profit", 0.10, 0.22, 0.10, 0.35,
    ),
    "event_driven": StrategyExecutionProfile(
        "event_driven", "事件驱动", "事件窗口", 66.0, "fixed_weight", "仅在事件仍有效且来源可追溯时加仓",
        "event_expiry_exit", 0.06, 0.12, 0.05, 0.10, event_expiry_minutes=7 * 24 * 60,
    ),
    "avoid": StrategyExecutionProfile(
        "avoid", "规避/观察", "不交易", 100.0, "cash_first_defensive", "禁止加仓",
        "major_negative_veto", None, None, None, 0.0,
    ),
}


STRATEGY_FAMILIES = {
    "short": StrategyFamily("short", "短线", "intraday_to_days", "score_weighted", "quick_stop_take_profit", "看分时、VWAP、量比和行为风险，小仓位快进快出。"),
    "swing": StrategyFamily("swing", "波段", "days_to_weeks", "atr_risk", "atr_trailing_stop", "看 MA20/MA60、MACD、板块强度和支撑压力。"),
    "position": StrategyFamily("position", "中长线", "months", "volatility_target", "thesis_break_exit", "看基本面、行业景气、长期趋势和重大负面。"),
    "dca": StrategyFamily("dca", "定投", "scheduled", "dca_schedule", "market_emergency_exit", "适用于 ETF 或长期资产，低估多买，高风险暂停。"),
    "core_satellite": StrategyFamily("core_satellite", "核心-卫星", "hybrid", "core_satellite", "staged_take_profit", "核心仓长期持有，卫星仓做短线增强。"),
    "event_driven": StrategyFamily("event_driven", "事件驱动", "event_window", "fixed_weight", "event_expiry_exit", "公告、业绩、政策或行业催化驱动，事件过期退出。"),
    "avoid": StrategyFamily("avoid", "规避", "none", "cash_first_defensive", "major_negative_veto", "高风险或数据不足时只观察，不自动交易。"),
}

# Compatibility for stored V3.23 sessions. New records always use canonical keys.
for _alias, _canonical in STRATEGY_FAMILY_ALIASES.items():
    STRATEGY_FAMILIES.setdefault(_alias, STRATEGY_FAMILIES[_canonical])


def get_strategy_execution_profile(value: Any) -> StrategyExecutionProfile:
    return STRATEGY_EXECUTION_PROFILES[normalize_strategy_family(value)]
