from __future__ import annotations

from typing import Any

from quant_data.persistence.trading_store import TradingStore


class TradingAuditLogV323:
    def __init__(self, store: TradingStore | None = None) -> None:
        self.store = store or TradingStore()

    def record(self, event_type: str, payload: dict[str, Any], *, mode: str = "", symbol: str = "", session_id: str = "") -> dict[str, Any]:
        row = {"event_type": event_type, "payload": dict(payload or {}), "mode": mode, "symbol": symbol, "session_id": session_id}
        rid = self.store.put("audit_events", row, mode=mode, symbol=symbol, session_id=session_id)
        row["id"] = rid
        return row

    def list(self, *, mode: str = "", symbol: str = "", limit: int = 200) -> list[dict[str, Any]]:
        return self.store.list("audit_events", mode=mode, symbol=symbol, limit=limit)
