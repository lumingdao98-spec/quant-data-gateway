from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from hashlib import sha256
import json
from typing import Any

from quant_data.persistence.trading_store import TradingStore


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass(slots=True)
class LedgerEntry:
    ledger_id: str
    mode: str
    session_id: str
    account_id: str
    entry_type: str
    amount: float
    symbol: str = ""
    order_id: str = ""
    fill_id: str = ""
    side: str = ""
    quantity: float = 0.0
    price: float = 0.0
    fee: float = 0.0
    tax: float = 0.0
    slippage: float = 0.0
    currency: str = "CNY"
    occurred_at: str = field(default_factory=_now)
    created_at: str = field(default_factory=_now)
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["entry_id"] = self.ledger_id
        return data


class LedgerService:
    def __init__(self, store: TradingStore) -> None:
        self.store = store

    def record_fill(self, fill: dict[str, Any], *, mode: str, session_id: str, account_id: str = "", source: str = "") -> list[dict[str, Any]]:
        data = dict(fill or {})
        fill_id = str(data.get("fill_id") or data.get("trade_id") or data.get("broker_trade_id") or "")
        order_id = str(data.get("order_id") or data.get("broker_order_id") or "")
        side = str(data.get("side") or "").lower()
        quantity = _num(data.get("quantity"))
        price = _num(data.get("price"))
        gross = _num(data.get("amount"), quantity * price)
        fee = abs(_num(data.get("fee")))
        tax = abs(_num(data.get("tax")))
        slippage = abs(_num(data.get("slippage")))
        occurred_at = str(data.get("filled_at") or data.get("occurred_at") or _now())
        common = {
            "mode": mode,
            "session_id": session_id,
            "account_id": account_id,
            "symbol": str(data.get("symbol") or ""),
            "order_id": order_id,
            "fill_id": fill_id,
            "side": side,
            "quantity": quantity,
            "price": price,
            "occurred_at": occurred_at,
            "source": source or str(data.get("source") or ""),
        }
        if fill_id:
            existing = [
                row
                for row in self.store.list_normalized(
                    "ledger_entries",
                    mode=mode,
                    session_id=session_id,
                    account_id=account_id,
                    limit=10000,
                )
                if str(row.get("fill_id") or "") == fill_id
            ]
            if existing:
                return existing
        entries = [self._entry({**common, "entry_type": side if side in {"buy", "sell"} else "cash_adjustment", "amount": gross if side == "sell" else -gross})]
        for entry_type, value in (("commission", fee), ("tax", tax), ("slippage", slippage)):
            if value > 0:
                entries.append(self._entry({**common, "entry_type": entry_type, "amount": -value, entry_type if entry_type != "commission" else "fee": value}))
        realized_pnl = self._apply_fill_to_lots(data, common=common)
        if side == "sell" and realized_pnl is not None:
            entries.append(
                self._entry(
                    {
                        **common,
                        "entry_type": "realized_pnl",
                        "amount": realized_pnl,
                    }
                )
            )
        for entry in entries:
            self.store.put_normalized("ledger_entries", entry, record_id=entry["ledger_id"])
        return entries

    def _apply_fill_to_lots(self, fill: dict[str, Any], *, common: dict[str, Any]) -> float | None:
        side = str(common.get("side") or "")
        quantity = _num(common.get("quantity"))
        price = _num(common.get("price"))
        symbol = str(common.get("symbol") or "")
        if not symbol or quantity <= 0 or price <= 0:
            return None
        if side == "buy":
            lot_id = sha256(
                f"{common.get('mode')}|{common.get('session_id')}|{common.get('fill_id')}|{symbol}".encode("utf-8")
            ).hexdigest()[:24]
            self.store.put_normalized(
                "position_lots",
                {
                    "lot_id": lot_id,
                    "mode": common.get("mode"),
                    "session_id": common.get("session_id"),
                    "account_id": common.get("account_id"),
                    "symbol": symbol,
                    "opened_at": common.get("occurred_at"),
                    "original_quantity": quantity,
                    "remaining_quantity": quantity,
                    "cost_price": price,
                    "source_order_id": common.get("order_id"),
                    "source_fill_id": common.get("fill_id"),
                    "status": "open",
                    "updated_at": common.get("occurred_at"),
                },
                record_id=lot_id,
            )
            return None
        if side != "sell":
            return None
        lots = list(
            reversed(
                self.store.list_normalized(
                    "position_lots",
                    mode=str(common.get("mode") or ""),
                    symbol=symbol,
                    session_id=str(common.get("session_id") or ""),
                    account_id=str(common.get("account_id") or ""),
                    status="open",
                    limit=10000,
                )
            )
        )
        remaining = quantity
        realized = 0.0
        matched_total = 0.0
        for lot in lots:
            available = _num(lot.get("remaining_quantity"))
            if available <= 0 or remaining <= 0:
                continue
            matched = min(available, remaining)
            matched_total += matched
            realized += matched * (price - _num(lot.get("cost_price")))
            new_remaining = max(0.0, available - matched)
            lot.update(
                {
                    "remaining_quantity": new_remaining,
                    "status": "closed" if new_remaining <= 0 else "open",
                    "closed_at": common.get("occurred_at") if new_remaining <= 0 else "",
                    "updated_at": common.get("occurred_at"),
                }
            )
            self.store.put_normalized(
                "position_lots",
                lot,
                record_id=str(lot.get("lot_id") or ""),
            )
            remaining -= matched
        return round(realized, 8) if matched_total > 0 else None

    def _entry(self, payload: dict[str, Any]) -> dict[str, Any]:
        identity = json.dumps(
            [payload.get("mode"), payload.get("session_id"), payload.get("fill_id"), payload.get("entry_type")],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        entry = LedgerEntry(ledger_id=sha256(identity.encode("utf-8")).hexdigest()[:24], **payload)
        return entry.to_dict()


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except Exception:
        return default
