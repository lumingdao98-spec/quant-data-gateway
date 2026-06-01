from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime
from typing import Any


DISCLAIMER = "研究辅助，不构成投资建议"


def _iso(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, list):
        return [_iso(x) for x in value]
    if isinstance(value, dict):
        return {str(k): _iso(v) for k, v in value.items()}
    if is_dataclass(value):
        return _iso(asdict(value))
    return value


def as_dict(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return _iso(asdict(value))
    if isinstance(value, dict):
        return _iso(value)
    raise TypeError(f"Unsupported value for as_dict: {type(value)!r}")


@dataclass(slots=True)
class BacktestConfig:
    run_id: str | None = None
    strategy: str = "score_rank_rebalance"
    symbols: list[str] = field(default_factory=list)
    start: str | None = None
    end: str | None = None
    frame: str = "1d"
    adjust: str = "qfq"
    initial_cash: float = 100_000.0
    benchmark: str = "000300"
    warmup_bars: int = 60
    frequency: str = "daily"
    rebalance_frequency: str = "daily"
    max_positions: int = 5
    max_single_position_pct: float = 0.25
    cash_reserve_pct: float = 0.02
    position_pct: float = 1.0
    sizing: str = "score_weighted"
    lot_size: int = 100
    t_plus_one: bool = True
    allow_short: bool = False
    order_type: str = "next_open"
    commission_rate: float = 0.0003
    min_commission: float = 5.0
    stamp_tax_rate: float = 0.001
    transfer_fee_rate: float = 0.00001
    slippage_bps: float = 5.0
    volume_limit_pct: float = 0.10
    stop_loss_pct: float = 8.0
    take_profit_pct: float = 0.0
    trailing_stop_pct: float = 0.0
    buy_score: float = 62.0
    sell_score: float = 48.0
    market_sentiment_weight: float = 0.06
    risk_budget_pct: float = 0.02
    use_screener_snapshot: bool = True
    screener_snapshot_id: str | None = None
    notes: list[str] = field(default_factory=list)
    disclaimer: str = DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return as_dict(self)


@dataclass(slots=True)
class StrategySignal:
    symbol: str
    date: str
    action: str
    score: float = 0.0
    strength: float = 0.0
    target_weight: float = 0.0
    price: float | None = None
    reason: str = ""
    source: str = "strategy"
    grade: str = ""
    risk_flags: list[str] = field(default_factory=list)
    features: dict[str, Any] = field(default_factory=dict)
    snapshot_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return as_dict(self)


@dataclass(slots=True)
class Order:
    order_id: str
    symbol: str
    date: str
    side: str
    quantity: int = 0
    target_weight: float | None = None
    order_type: str = "next_open"
    limit_price: float | None = None
    signal_date: str | None = None
    signal_score: float | None = None
    reason: str = ""
    status: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return as_dict(self)


@dataclass(slots=True)
class Fill:
    fill_id: str
    order_id: str
    symbol: str
    date: str
    side: str
    quantity: int
    requested_quantity: int
    price: float
    gross_amount: float
    commission: float = 0.0
    stamp_tax: float = 0.0
    transfer_fee: float = 0.0
    slippage_cost: float = 0.0
    reason: str = ""
    partial: bool = False
    blocked: bool = False

    @property
    def total_cost(self) -> float:
        return self.commission + self.stamp_tax + self.transfer_fee + self.slippage_cost

    def to_dict(self) -> dict[str, Any]:
        data = as_dict(self)
        data["total_cost"] = round(self.total_cost, 6)
        return data


@dataclass(slots=True)
class Position:
    symbol: str
    quantity: int = 0
    available_quantity: int = 0
    avg_cost: float = 0.0
    last_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    entry_date: str | None = None
    highest_price: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return as_dict(self)


@dataclass(slots=True)
class PortfolioState:
    date: str
    cash: float
    market_value: float
    equity: float
    positions: dict[str, Position] = field(default_factory=dict)
    daily_return: float = 0.0
    turnover: float = 0.0
    leverage: float = 0.0
    exposure: float = 0.0
    cost: float = 0.0
    benchmark_return: float | None = None

    def to_dict(self) -> dict[str, Any]:
        data = as_dict(self)
        data["positions"] = {k: v.to_dict() if isinstance(v, Position) else _iso(v) for k, v in self.positions.items()}
        return data


@dataclass(slots=True)
class Trade:
    symbol: str
    entry_date: str
    exit_date: str | None
    entry_price: float
    exit_price: float | None
    quantity: int
    entry_reason: str = ""
    exit_reason: str = ""
    entry_signal_score: float | None = None
    exit_signal_score: float | None = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    bars_held: int = 0
    costs: float = 0.0
    max_favorable_excursion_pct: float = 0.0
    max_adverse_excursion_pct: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return as_dict(self)


@dataclass(slots=True)
class BacktestResult:
    run_id: str
    config: BacktestConfig
    status: str
    started_at: str
    ended_at: str
    symbols: list[str]
    orders: list[Order] = field(default_factory=list)
    fills: list[Fill] = field(default_factory=list)
    trades: list[Trade] = field(default_factory=list)
    portfolio_states: list[PortfolioState] = field(default_factory=list)
    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    data_quality: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    cache_status: str = "memory"
    disclaimer: str = DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "symbols": self.symbols,
            "config": self.config.to_dict(),
            "orders": [x.to_dict() for x in self.orders],
            "fills": [x.to_dict() for x in self.fills],
            "trades": [x.to_dict() for x in self.trades],
            "portfolio_states": [x.to_dict() for x in self.portfolio_states],
            "equity_curve": _iso(self.equity_curve),
            "metrics": _iso(self.metrics),
            "data_quality": _iso(self.data_quality),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "cache_status": self.cache_status,
            "disclaimer": self.disclaimer,
        }
