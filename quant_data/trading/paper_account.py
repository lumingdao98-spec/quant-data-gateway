from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class PaperAccountPosition:
    symbol: str
    quantity: int = 0
    available_quantity: int = 0
    avg_cost: float = 0.0
    market_price: float = 0.0
    market_value: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    industry: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PaperFill:
    order_id: str
    symbol: str
    side: str
    quantity: int
    price: float
    amount: float
    fee: float = 0.0
    slippage: float = 0.0
    realized_pnl: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PaperAccount:
    def __init__(self, initial_cash: float = 100_000.0, *, account_mode: str = "hybrid") -> None:
        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.frozen_cash = 0.0
        self.positions: dict[str, PaperAccountPosition] = {}
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.daily_pnl = 0.0
        self.max_drawdown = 0.0
        self.trade_count_today = 0
        self.win_loss_streak = 0
        self.account_mode = account_mode
        self.equity_high = float(initial_cash)
        self.fills: list[PaperFill] = []

    @classmethod
    def from_snapshot(
        cls,
        snapshot: dict[str, Any] | None,
        *,
        fills: list[dict[str, Any]] | None = None,
    ) -> "PaperAccount":
        """Restore one paper account without replaying historical fills.

        Account snapshots are authoritative for cash and positions. Replaying
        fills here would debit cash twice after a service restart.
        """

        data = dict(snapshot or {})
        account = cls(
            initial_cash=_float(data.get("initial_cash"), 100_000.0),
            account_mode=str(data.get("account_mode") or "hybrid"),
        )
        account.cash = _float(data.get("cash"), account.initial_cash)
        account.frozen_cash = _float(data.get("frozen_cash"), 0.0)
        account.realized_pnl = _float(data.get("realized_pnl"), 0.0)
        account.unrealized_pnl = _float(data.get("unrealized_pnl"), 0.0)
        account.daily_pnl = _float(data.get("daily_pnl"), 0.0)
        account.max_drawdown = _float(data.get("max_drawdown"), 0.0)
        account.trade_count_today = int(_float(data.get("trade_count_today"), 0.0))
        account.win_loss_streak = int(_float(data.get("win_loss_streak"), 0.0))
        positions = data.get("positions") if isinstance(data.get("positions"), dict) else {}
        for symbol, raw in positions.items():
            item = dict(raw or {})
            qty = int(_float(item.get("quantity"), 0.0))
            if qty <= 0:
                continue
            account.positions[str(symbol)] = PaperAccountPosition(
                symbol=str(item.get("symbol") or symbol),
                quantity=qty,
                available_quantity=int(_float(item.get("available_quantity"), qty)),
                avg_cost=_float(item.get("avg_cost"), 0.0),
                market_price=_float(item.get("market_price"), 0.0),
                market_value=_float(item.get("market_value"), 0.0),
                realized_pnl=_float(item.get("realized_pnl"), 0.0),
                unrealized_pnl=_float(item.get("unrealized_pnl"), 0.0),
                industry=str(item.get("industry") or ""),
            )
        account.fills = []
        for raw in fills or []:
            item = dict(raw or {})
            try:
                account.fills.append(
                    PaperFill(
                        order_id=str(item.get("order_id") or ""),
                        symbol=str(item.get("symbol") or ""),
                        side=str(item.get("side") or ""),
                        quantity=int(_float(item.get("quantity"), 0.0)),
                        price=_float(item.get("price"), 0.0),
                        amount=_float(item.get("amount"), 0.0),
                        fee=_float(item.get("fee"), 0.0),
                        slippage=_float(item.get("slippage"), 0.0),
                        realized_pnl=_float(item.get("realized_pnl"), 0.0),
                        created_at=str(item.get("created_at") or item.get("filled_at") or datetime.now().isoformat(timespec="seconds")),
                    )
                )
            except (TypeError, ValueError):
                continue
        account.equity_high = max(_float(data.get("equity"), account.equity), account.equity)
        return account

    @property
    def market_value(self) -> float:
        return sum(p.market_value for p in self.positions.values())

    @property
    def equity(self) -> float:
        return self.cash + self.market_value

    @property
    def available_cash(self) -> float:
        return max(0.0, self.cash - self.frozen_cash)

    def snapshot(self) -> dict[str, Any]:
        return {
            "initial_cash": round(self.initial_cash, 6),
            "cash": round(self.cash, 6),
            "equity": round(self.equity, 6),
            "market_value": round(self.market_value, 6),
            "available_cash": round(self.available_cash, 6),
            "frozen_cash": round(self.frozen_cash, 6),
            "realized_pnl": round(self.realized_pnl, 6),
            "unrealized_pnl": round(self.unrealized_pnl, 6),
            "daily_pnl": round(self.daily_pnl, 6),
            "max_drawdown": round(self.max_drawdown, 6),
            "trade_count_today": self.trade_count_today,
            "win_loss_streak": self.win_loss_streak,
            "account_mode": self.account_mode,
            "positions": {k: v.to_dict() for k, v in self.positions.items()},
            "available_quantity": {k: v.available_quantity for k, v in self.positions.items()},
            "total_return_pct": round((self.equity / self.initial_cash - 1.0) * 100 if self.initial_cash else 0.0, 6),
        }

    def mark_to_market(self, prices: dict[str, float] | None = None) -> dict[str, Any]:
        prices = prices or {}
        unrealized = 0.0
        for symbol, pos in list(self.positions.items()):
            price = float(prices.get(symbol) or pos.market_price or pos.avg_cost or 0.0)
            pos.market_price = price
            pos.market_value = price * pos.quantity
            pos.unrealized_pnl = (price - pos.avg_cost) * pos.quantity
            unrealized += pos.unrealized_pnl
        self.unrealized_pnl = unrealized
        self.equity_high = max(self.equity_high, self.equity)
        if self.equity_high > 0:
            self.max_drawdown = min(self.max_drawdown, self.equity / self.equity_high - 1.0)
        return self.snapshot()

    def apply_fill(self, fill: PaperFill) -> dict[str, Any]:
        if fill.quantity <= 0:
            return self.snapshot()
        pos = self.positions.get(fill.symbol, PaperAccountPosition(symbol=fill.symbol))
        if fill.side == "buy":
            total_cost = pos.avg_cost * pos.quantity + fill.amount + fill.fee + fill.slippage
            pos.quantity += fill.quantity
            pos.available_quantity += fill.quantity
            pos.avg_cost = total_cost / max(1, pos.quantity)
            pos.market_price = fill.price
            pos.market_value = pos.quantity * fill.price
            self.cash -= fill.amount + fill.fee + fill.slippage
        else:
            qty = min(fill.quantity, pos.quantity)
            fill.quantity = qty
            fill.amount = qty * fill.price
            fill.realized_pnl = (fill.price - pos.avg_cost) * qty - fill.fee - fill.slippage
            pos.quantity -= qty
            pos.available_quantity = max(0, pos.available_quantity - qty)
            pos.market_price = fill.price
            pos.market_value = pos.quantity * fill.price
            pos.realized_pnl += fill.realized_pnl
            self.realized_pnl += fill.realized_pnl
            self.cash += fill.amount - fill.fee - fill.slippage
            self.win_loss_streak = self.win_loss_streak + 1 if fill.realized_pnl >= 0 else self.win_loss_streak - 1
        if pos.quantity <= 0:
            self.positions.pop(fill.symbol, None)
        else:
            self.positions[fill.symbol] = pos
        self.trade_count_today += 1
        self.fills.append(fill)
        self.mark_to_market({fill.symbol: fill.price})
        return self.snapshot()

    def fills_dicts(self) -> list[dict[str, Any]]:
        return [x.to_dict() for x in self.fills]


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "--"):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)
