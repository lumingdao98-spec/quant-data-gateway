from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


StrategyHorizon = Literal["intraday_paper", "short_term", "swing", "position", "dca", "hybrid"]


@dataclass(slots=True)
class StrategyHorizonConfig:
    horizon: StrategyHorizon = "swing"
    max_holding_days: int | None = None
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None
    rebalance_frequency: str | None = None
    primary_factors: list[str] = field(default_factory=list)
    allow_pyramid: bool = False
    allow_dca: bool = False
    require_market_confirm: bool = True

    def resolved_rules(self) -> dict[str, Any]:
        rules = _DEFAULT_RULES.get(self.horizon, _DEFAULT_RULES["swing"]).copy()
        overrides = {
            "max_holding_days": self.max_holding_days,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
            "rebalance_frequency": self.rebalance_frequency,
        }
        for key, value in overrides.items():
            if value is not None:
                rules[key] = value
        if self.primary_factors:
            rules["primary_factors"] = list(self.primary_factors)
        rules["allow_pyramid"] = bool(self.allow_pyramid or rules.get("allow_pyramid"))
        rules["allow_dca"] = bool(self.allow_dca or rules.get("allow_dca"))
        rules["require_market_confirm"] = bool(self.require_market_confirm)
        return rules

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["rules"] = self.resolved_rules()
        return data


_DEFAULT_RULES: dict[str, dict[str, Any]] = {
    "intraday_paper": {
        "max_holding_days": 1,
        "stop_loss_pct": 2.0,
        "take_profit_pct": 4.0,
        "rebalance_frequency": "tick",
        "primary_factors": ["intraday", "volume_ratio", "vwap", "anomaly_guard", "risk_gateway"],
        "description": "盘中模拟重视分时、量比、VWAP 和异常波动，非交易时段只允许回放。",
    },
    "short_term": {
        "max_holding_days": 5,
        "stop_loss_pct": 4.0,
        "take_profit_pct": 8.0,
        "rebalance_frequency": "daily",
        "primary_factors": ["momentum", "volume", "macd", "rsi_kdj", "anomaly_guard"],
        "description": "短线更重视动量和量价，禁止高位放量滞涨追买。",
    },
    "swing": {
        "max_holding_days": 20,
        "stop_loss_pct": 7.0,
        "take_profit_pct": 15.0,
        "rebalance_frequency": "daily",
        "primary_factors": ["ma20", "ma60", "sector_strength", "atr_stop", "fund_flow"],
        "description": "中线重视 MA20/MA60、板块强度和 ATR/MA20 止损。",
    },
    "position": {
        "max_holding_days": 120,
        "stop_loss_pct": 12.0,
        "take_profit_pct": 0.0,
        "rebalance_frequency": "weekly",
        "primary_factors": ["fundamental", "valuation", "industry_cycle", "market_regime"],
        "description": "长线重视基本面、估值和行业景气，降低短线噪声权重。",
    },
    "dca": {
        "max_holding_days": 0,
        "stop_loss_pct": 0.0,
        "take_profit_pct": 0.0,
        "rebalance_frequency": "monthly",
        "primary_factors": ["valuation_level", "etf_liquidity", "market_regime"],
        "allow_dca": True,
        "description": "定投按固定周期和金额执行，可低估加倍、高估减半。",
    },
    "hybrid": {
        "max_holding_days": 60,
        "stop_loss_pct": 8.0,
        "take_profit_pct": 12.0,
        "rebalance_frequency": "daily",
        "primary_factors": ["core_fundamental", "satellite_technical", "signal_fusion", "risk_gateway"],
        "allow_dca": True,
        "allow_pyramid": True,
        "description": "混合模式由核心仓长期/定投，卫星仓按短线评分交易。",
    },
}
