from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class AccountSnapshot:
    initial_cash: float
    cash: float
    market_value: float
    equity: float
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    available_cash: float = 0.0
    frozen_cash: float = 0.0
    reserved_cash: float = 0.0
    reinvestable_cash: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CashLedgerEntry:
    date: str
    action: str
    cash_before: float
    cash_after: float
    equity_before: float
    equity_after: float
    realized_pnl: float = 0.0
    fee: float = 0.0
    tax: float = 0.0
    slippage: float = 0.0
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MoneyManager:
    def __init__(
        self,
        initial_cash: float = 100_000.0,
        *,
        compound_returns: bool = True,
        cash_reserve_pct: float = 0.02,
    ) -> None:
        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.market_value = 0.0
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.frozen_cash = 0.0
        self.cash_reserve_pct = float(cash_reserve_pct)
        self.compound_returns = bool(compound_returns)
        self.ledger: list[CashLedgerEntry] = []

    @property
    def equity(self) -> float:
        return self.cash + self.market_value

    @property
    def reserved_cash(self) -> float:
        base = self.equity if self.compound_returns else self.initial_cash
        return max(0.0, base * self.cash_reserve_pct)

    @property
    def available_cash(self) -> float:
        return max(0.0, self.cash - self.frozen_cash - self.reserved_cash)

    @property
    def reinvestable_cash(self) -> float:
        if self.compound_returns:
            return self.available_cash
        return max(0.0, min(self.available_cash, self.initial_cash - self.market_value))

    def snapshot(self) -> AccountSnapshot:
        return AccountSnapshot(
            initial_cash=round(self.initial_cash, 6),
            cash=round(self.cash, 6),
            market_value=round(self.market_value, 6),
            equity=round(self.equity, 6),
            realized_pnl=round(self.realized_pnl, 6),
            unrealized_pnl=round(self.unrealized_pnl, 6),
            available_cash=round(self.available_cash, 6),
            frozen_cash=round(self.frozen_cash, 6),
            reserved_cash=round(self.reserved_cash, 6),
            reinvestable_cash=round(self.reinvestable_cash, 6),
        )

    def mark_to_market(self, market_value: float, unrealized_pnl: float = 0.0) -> AccountSnapshot:
        self.market_value = max(0.0, float(market_value or 0.0))
        self.unrealized_pnl = float(unrealized_pnl or 0.0)
        return self.snapshot()

    def apply_buy(self, amount: float, fee: float = 0.0, slippage: float = 0.0, *, date: str | None = None, reason: str = "") -> CashLedgerEntry:
        return self._apply_cash_change(
            action="buy",
            cash_delta=-(float(amount or 0.0) + float(fee or 0.0) + float(slippage or 0.0)),
            realized_pnl=0.0,
            fee=fee,
            tax=0.0,
            slippage=slippage,
            date=date,
            reason=reason,
        )

    def apply_sell(
        self,
        amount: float,
        realized_pnl: float = 0.0,
        fee: float = 0.0,
        tax: float = 0.0,
        slippage: float = 0.0,
        *,
        date: str | None = None,
        reason: str = "",
    ) -> CashLedgerEntry:
        self.realized_pnl += float(realized_pnl or 0.0)
        return self._apply_cash_change(
            action="sell",
            cash_delta=float(amount or 0.0) - float(fee or 0.0) - float(tax or 0.0) - float(slippage or 0.0),
            realized_pnl=realized_pnl,
            fee=fee,
            tax=tax,
            slippage=slippage,
            date=date,
            reason=reason,
        )

    def _apply_cash_change(
        self,
        *,
        action: str,
        cash_delta: float,
        realized_pnl: float,
        fee: float,
        tax: float,
        slippage: float,
        date: str | None,
        reason: str,
    ) -> CashLedgerEntry:
        cash_before = self.cash
        equity_before = self.equity
        self.cash += cash_delta
        entry = CashLedgerEntry(
            date=date or datetime.now().isoformat(timespec="seconds"),
            action=action,
            cash_before=round(cash_before, 6),
            cash_after=round(self.cash, 6),
            equity_before=round(equity_before, 6),
            equity_after=round(self.equity, 6),
            realized_pnl=round(float(realized_pnl or 0.0), 6),
            fee=round(float(fee or 0.0), 6),
            tax=round(float(tax or 0.0), 6),
            slippage=round(float(slippage or 0.0), 6),
            reason=reason,
        )
        self.ledger.append(entry)
        return entry

    def ledger_dicts(self) -> list[dict[str, Any]]:
        return [x.to_dict() for x in self.ledger]
