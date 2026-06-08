from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


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


STRATEGY_FAMILIES = {
    "short_term": StrategyFamily("short_term", "短线", "intraday_to_days", "score_weighted", "quick_stop_take_profit", "看分时/VWAP/量比/行为风险，小仓位快进快出。"),
    "swing": StrategyFamily("swing", "波段", "days_to_weeks", "atr_risk", "atr_trailing_stop", "看 MA20/MA60/MACD/板块强度和支撑压力。"),
    "long_term": StrategyFamily("long_term", "长线", "months", "core_satellite", "thesis_break_exit", "看基本面、行业景气、长期趋势和重大负面。"),
    "dca": StrategyFamily("dca", "定投", "scheduled", "dca_schedule", "market_emergency_exit", "适用于 ETF 或长期资产，低估多买，高风险暂停。"),
    "core_satellite": StrategyFamily("core_satellite", "核心-卫星", "hybrid", "core_satellite", "staged_take_profit", "核心长期持有，卫星仓做短线增强。"),
    "event_driven": StrategyFamily("event_driven", "事件驱动", "event_window", "fixed_weight", "event_expiry_exit", "公告/业绩/政策/行业催化驱动，事件过期退出。"),
    "avoid": StrategyFamily("avoid", "规避", "none", "cash_first_defensive", "major_negative_veto", "高风险或数据不足，不自动交易。"),
}
