from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json
import sqlite3

from .data_contracts import raw_hash, utc_now_text


@dataclass(slots=True)
class PITRecord:
    record_id: str
    symbol: str
    dataset: str
    decision_time: str
    available_at: str
    payload: dict[str, Any]
    source_id: str = "cache"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PITStore:
    def __init__(self, db_path: str | Path = "data/v323_trading_store.sqlite") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS pit_records (
                    record_id TEXT PRIMARY KEY,
                    symbol TEXT,
                    dataset TEXT,
                    decision_time TEXT,
                    available_at TEXT,
                    source_id TEXT,
                    payload_json TEXT,
                    created_at TEXT
                )
                """
            )

    def put(self, record: PITRecord) -> PITRecord:
        payload = json.dumps(record.payload, ensure_ascii=False, sort_keys=True)
        rid = record.record_id or f"pit-{raw_hash([record.symbol, record.dataset, record.decision_time, payload])}"
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                "INSERT OR REPLACE INTO pit_records VALUES (?,?,?,?,?,?,?,?)",
                (rid, record.symbol, record.dataset, record.decision_time, record.available_at, record.source_id, payload, utc_now_text()),
            )
        return PITRecord(**{**record.to_dict(), "record_id": rid})

    def latest(self, symbol: str, dataset: str, decision_time: str) -> PITRecord | None:
        with sqlite3.connect(self.db_path) as con:
            row = con.execute(
                """
                SELECT record_id, symbol, dataset, decision_time, available_at, source_id, payload_json
                FROM pit_records
                WHERE symbol=? AND dataset=? AND available_at<=?
                ORDER BY available_at DESC, created_at DESC
                LIMIT 1
                """,
                (symbol, dataset, decision_time),
            ).fetchone()
        if not row:
            return None
        return PITRecord(row[0], row[1], row[2], row[3], row[4], json.loads(row[6] or "{}"), row[5])

    def stats(self) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as con:
            rows = con.execute("SELECT dataset, COUNT(*) FROM pit_records GROUP BY dataset").fetchall()
        return {"db_path": str(self.db_path), "datasets": {k: v for k, v in rows}}
