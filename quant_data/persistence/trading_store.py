from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import sqlite3

from quant_data.data.data_contracts import raw_hash, utc_now_text


TABLES = (
    "signals",
    "score_provenance",
    "risk_checks",
    "orders",
    "fills",
    "positions",
    "account_snapshots",
    "broker_raw_responses",
    "chart_markers",
    "audit_events",
    "data_source_status",
    "manual_confirmations",
    "paper_sessions",
    "live_sessions",
)


class TradingStore:
    def __init__(self, db_path: str | Path = "data/v323_trading_store.sqlite") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.db_path) as con:
            for table in TABLES:
                con.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        id TEXT PRIMARY KEY,
                        mode TEXT,
                        symbol TEXT,
                        session_id TEXT,
                        created_at TEXT,
                        payload_json TEXT
                    )
                    """
                )

    def put(self, table: str, payload: dict[str, Any], *, mode: str = "", symbol: str = "", session_id: str = "", record_id: str = "") -> str:
        if table not in TABLES:
            raise ValueError(f"unsupported trading store table: {table}")
        payload = dict(payload or {})
        rid = record_id or str(payload.get("id") or payload.get("order_id") or payload.get("fill_id") or payload.get("provenance_id") or raw_hash([table, payload, utc_now_text()]))
        created = str(payload.get("created_at") or payload.get("timestamp") or utc_now_text())
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                f"INSERT OR REPLACE INTO {table} VALUES (?,?,?,?,?,?)",
                (rid, mode or str(payload.get("mode") or ""), symbol or str(payload.get("symbol") or ""), session_id or str(payload.get("session_id") or ""), created, json.dumps(payload, ensure_ascii=False, sort_keys=True)),
            )
        return rid

    def get(self, table: str, record_id: str) -> dict[str, Any] | None:
        if table not in TABLES:
            raise ValueError(f"unsupported trading store table: {table}")
        with sqlite3.connect(self.db_path) as con:
            row = con.execute(f"SELECT id, mode, symbol, session_id, created_at, payload_json FROM {table} WHERE id=?", (record_id,)).fetchone()
        if not row:
            return None
        payload = json.loads(row[5] or "{}")
        payload.setdefault("id", row[0])
        payload.setdefault("mode", row[1])
        payload.setdefault("symbol", row[2])
        payload.setdefault("session_id", row[3])
        payload.setdefault("created_at", row[4])
        return payload

    def list(self, table: str, *, mode: str = "", symbol: str = "", session_id: str = "", limit: int = 200) -> list[dict[str, Any]]:
        if table not in TABLES:
            raise ValueError(f"unsupported trading store table: {table}")
        where = []
        params: list[Any] = []
        if mode:
            where.append("mode=?")
            params.append(mode)
        if symbol:
            where.append("symbol=?")
            params.append(symbol)
        if session_id:
            where.append("session_id=?")
            params.append(session_id)
        sql = f"SELECT id, mode, symbol, session_id, created_at, payload_json FROM {table}"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(max(1, int(limit or 200)))
        with sqlite3.connect(self.db_path) as con:
            rows = con.execute(sql, params).fetchall()
        out = []
        for row in rows:
            payload = json.loads(row[5] or "{}")
            payload.setdefault("id", row[0])
            payload.setdefault("mode", row[1])
            payload.setdefault("symbol", row[2])
            payload.setdefault("session_id", row[3])
            payload.setdefault("created_at", row[4])
            out.append(payload)
        return out

    def stats(self) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as con:
            counts = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in TABLES}
        return {"db_path": str(self.db_path), "tables": counts}
