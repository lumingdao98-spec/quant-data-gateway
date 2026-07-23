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
    "position_reviews",
    "position_review_runs",
)

NORMALIZED_TABLE_SCHEMAS = {
    "ledger_entries": """
        ledger_id TEXT PRIMARY KEY, entry_id TEXT, mode TEXT, session_id TEXT, account_id TEXT,
        order_id TEXT, fill_id TEXT, symbol TEXT, entry_type TEXT, side TEXT,
        quantity REAL, price REAL, amount REAL, fee REAL, tax REAL, slippage REAL,
        currency TEXT, occurred_at TEXT, created_at TEXT, source TEXT, payload_json TEXT
    """,
    "broker_accounts": """
        snapshot_id TEXT PRIMARY KEY, mode TEXT, session_id TEXT, broker TEXT, account_id TEXT,
        initial_cash REAL, cash REAL, equity REAL, market_value REAL, available_cash REAL,
        frozen_cash REAL, total_cash REAL, position_market_value REAL, total_equity REAL,
        realized_pnl REAL, unrealized_pnl REAL, daily_pnl REAL, max_drawdown REAL,
        authorized INTEGER, fetched_at TEXT, available_at TEXT,
        source TEXT, quality_status TEXT, payload_json TEXT
    """,
    "broker_positions": """
        record_id TEXT PRIMARY KEY, snapshot_id TEXT, session_id TEXT, account_id TEXT,
        broker TEXT, symbol TEXT, name TEXT, quantity REAL, available_quantity REAL,
        avg_cost REAL, market_price REAL, market_value REAL, unrealized_pnl REAL,
        unrealized_pnl_pct REAL, fetched_at TEXT, source TEXT, payload_json TEXT
    """,
    "broker_orders": """
        record_id TEXT PRIMARY KEY, session_id TEXT, account_id TEXT, broker TEXT,
        broker_order_id TEXT, order_id TEXT, symbol TEXT, side TEXT, status TEXT,
        quantity REAL, price REAL, filled_quantity REAL, created_at TEXT, updated_at TEXT,
        source TEXT, payload_json TEXT
    """,
    "broker_trades": """
        record_id TEXT PRIMARY KEY, session_id TEXT, account_id TEXT, broker TEXT,
        broker_trade_id TEXT, broker_order_id TEXT, order_id TEXT, symbol TEXT, side TEXT,
        quantity REAL, price REAL, amount REAL, fee REAL, tax REAL, slippage REAL,
        filled_at TEXT, source TEXT, payload_json TEXT
    """,
    "account_equity_curve": """
        point_id TEXT PRIMARY KEY, mode TEXT, session_id TEXT, account_id TEXT,
        equity REAL, available_cash REAL, position_market_value REAL, realized_pnl REAL,
        unrealized_pnl REAL, return_pct REAL, timestamp TEXT, source TEXT, payload_json TEXT
    """,
    "position_lots": """
        lot_id TEXT PRIMARY KEY, mode TEXT, session_id TEXT, account_id TEXT, symbol TEXT,
        opened_at TEXT, closed_at TEXT, original_quantity REAL, remaining_quantity REAL,
        cost_price REAL, source_order_id TEXT, source_fill_id TEXT, status TEXT,
        updated_at TEXT, payload_json TEXT
    """,
}


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
            for table, schema in NORMALIZED_TABLE_SCHEMAS.items():
                con.execute(f"CREATE TABLE IF NOT EXISTS {table} ({schema})")
            migrations = {
                "ledger_entries": {"entry_id": "TEXT"},
                "broker_accounts": {
                    "mode": "TEXT",
                    "initial_cash": "REAL", "cash": "REAL", "equity": "REAL", "market_value": "REAL",
                    "realized_pnl": "REAL", "unrealized_pnl": "REAL", "daily_pnl": "REAL", "max_drawdown": "REAL",
                },
            }
            for table, columns in migrations.items():
                existing = {str(row[1]) for row in con.execute(f"PRAGMA table_info({table})").fetchall()}
                for column, column_type in columns.items():
                    if column not in existing:
                        con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
            con.execute("CREATE INDEX IF NOT EXISTS idx_ledger_mode_symbol_time ON ledger_entries(mode, symbol, occurred_at)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_broker_positions_session_symbol ON broker_positions(session_id, symbol, fetched_at)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_broker_orders_session_status ON broker_orders(session_id, status, updated_at)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_broker_trades_session_symbol ON broker_trades(session_id, symbol, filled_at)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_equity_session_time ON account_equity_curve(session_id, timestamp)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_broker_accounts_mode_session ON broker_accounts(mode, session_id, fetched_at)")

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
        # Many trading events share second-level timestamps. rowid keeps the
        # most recently persisted snapshot first instead of returning an older
        # cash/position snapshot from the same second.
        sql += " ORDER BY created_at DESC, rowid DESC LIMIT ?"
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

    def delete(self, table: str, *, mode: str = "", symbol: str = "", session_id: str = "", record_id: str = "") -> int:
        if table not in TABLES:
            raise ValueError(f"unsupported trading store table: {table}")
        where = []
        params: list[Any] = []
        for column, value in (("id", record_id), ("mode", mode), ("symbol", symbol), ("session_id", session_id)):
            if value:
                where.append(f"{column}=?")
                params.append(value)
        if not where:
            raise ValueError("refusing to delete a trading table without filters")
        with sqlite3.connect(self.db_path) as con:
            cur = con.execute(f"DELETE FROM {table} WHERE " + " AND ".join(where), params)
            return int(cur.rowcount or 0)

    def put_normalized(self, table: str, payload: dict[str, Any], *, record_id: str = "") -> str:
        if table not in NORMALIZED_TABLE_SCHEMAS:
            raise ValueError(f"unsupported normalized trading table: {table}")
        data = dict(payload or {})
        columns = self._normalized_columns(table)
        id_column = columns[0]
        rid = str(
            record_id
            or data.get(id_column)
            or data.get("id")
            or data.get("ledger_id")
            or data.get("snapshot_id")
            or data.get("record_id")
            or data.get("point_id")
            or data.get("lot_id")
            or raw_hash([table, data, utc_now_text()])
        )
        data[id_column] = rid
        if "payload_json" in columns:
            data["payload_json"] = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        values = [data.get(column) for column in columns]
        placeholders = ",".join("?" for _ in columns)
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                f"INSERT OR REPLACE INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                values,
            )
        return rid

    def list_normalized(
        self,
        table: str,
        *,
        mode: str = "",
        symbol: str = "",
        session_id: str = "",
        account_id: str = "",
        status: str = "",
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        if table not in NORMALIZED_TABLE_SCHEMAS:
            raise ValueError(f"unsupported normalized trading table: {table}")
        columns = self._normalized_columns(table)
        filters = {"mode": mode, "symbol": symbol, "session_id": session_id, "account_id": account_id, "status": status}
        where: list[str] = []
        params: list[Any] = []
        for column, value in filters.items():
            if value and column in columns:
                where.append(f"{column}=?")
                params.append(value)
        time_column = next((name for name in ("occurred_at", "filled_at", "updated_at", "fetched_at", "timestamp", "created_at") if name in columns), columns[0])
        sql = f"SELECT {','.join(columns)} FROM {table}"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += f" ORDER BY {time_column} DESC, rowid DESC LIMIT ?"
        params.append(max(1, min(int(limit or 200), 10000)))
        with sqlite3.connect(self.db_path) as con:
            rows = con.execute(sql, params).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            item = dict(zip(columns, row))
            raw = item.pop("payload_json", "")
            try:
                original = json.loads(raw or "{}")
            except Exception:
                original = {}
            original.update({key: value for key, value in item.items() if value is not None})
            out.append(original)
        return out

    def _normalized_columns(self, table: str) -> list[str]:
        with sqlite3.connect(self.db_path) as con:
            return [str(row[1]) for row in con.execute(f"PRAGMA table_info({table})").fetchall()]

    def stats(self) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as con:
            counts = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in (*TABLES, *NORMALIZED_TABLE_SCHEMAS)}
        return {"db_path": str(self.db_path), "tables": counts}
