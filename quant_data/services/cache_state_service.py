from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from quant_data.config import DATA_DIR


DEFAULT_TTLS = {
    "screener_snapshot": 30 * 60,
    "info_snapshot": 6 * 60 * 60,
    "kline_cache": 6 * 60 * 60,
    "quote_cache": 30,
    "technical_factor_cache": 6 * 60 * 60,
    "global_news_cache": 45 * 60,
}


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return str(value)


@dataclass(frozen=True)
class CacheRead:
    data: dict[str, Any] | None
    cache_status: dict[str, Any]


class CacheStateService:
    """统一的持久化缓存和快照状态层。

    这里不替代底层行情/K线缓存，而是把用户可见的页面状态、API快照和
    fallback 结果统一保存到 SQLite，方便前端恢复和展示缓存状态。
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or DATA_DIR / "cache_state.sqlite")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_state (
                    kind TEXT NOT NULL,
                    key TEXT NOT NULL,
                    symbol TEXT DEFAULT '',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    ttl_seconds INTEGER NOT NULL,
                    source TEXT DEFAULT '',
                    payload TEXT NOT NULL,
                    PRIMARY KEY(kind, key)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_state_kind_updated ON cache_state(kind, updated_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_state_symbol_updated ON cache_state(kind, symbol, updated_at DESC)")

    def ttl_for(self, kind: str, ttl_seconds: int | None = None) -> int:
        return int(ttl_seconds if ttl_seconds is not None else DEFAULT_TTLS.get(kind, 30 * 60))

    def status(self, state: str, *, key: str = "", created_at: float | None = None, ttl_seconds: int | None = None, source: str = "", error: str | None = None) -> dict[str, Any]:
        now = time.time()
        age = max(0.0, now - created_at) if created_at else None
        ttl = int(ttl_seconds or 0)
        return {
            "status": state,
            "snapshot_id": key or None,
            "created_at": datetime.fromtimestamp(created_at).isoformat(timespec="seconds") if created_at else None,
            "ttl_seconds": ttl,
            "age_seconds": round(age, 2) if age is not None else None,
            "source": source,
            "stale": bool(age is not None and ttl and age > ttl),
            "error": error,
        }

    def put(self, kind: str, key: str, payload: dict[str, Any], *, ttl_seconds: int | None = None, symbol: str = "", source: str = "") -> dict[str, Any]:
        ttl = self.ttl_for(kind, ttl_seconds)
        now = time.time()
        data = dict(payload or {})
        data.setdefault("snapshot_id", key)
        data.setdefault("created_at", datetime.fromtimestamp(now).isoformat(timespec="seconds"))
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO cache_state(kind,key,symbol,created_at,updated_at,ttl_seconds,source,payload)
                VALUES(?,?,?,?,?,?,?,?)
                ON CONFLICT(kind,key) DO UPDATE SET
                    symbol=excluded.symbol,
                    updated_at=excluded.updated_at,
                    ttl_seconds=excluded.ttl_seconds,
                    source=excluded.source,
                    payload=excluded.payload
                """,
                (kind, key, symbol or "", now, now, ttl, source, json.dumps(data, ensure_ascii=False, default=_json_default)),
            )
        return self.status("refreshed", key=key, created_at=now, ttl_seconds=ttl, source=source)

    def get(self, kind: str, key: str, *, allow_stale: bool = True, ttl_seconds: int | None = None) -> CacheRead:
        if not key:
            return CacheRead(None, self.status("miss", key=key, ttl_seconds=self.ttl_for(kind, ttl_seconds), source="cache_state"))
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM cache_state WHERE kind=? AND key=?", (kind, key)).fetchone()
        if not row:
            return CacheRead(None, self.status("miss", key=key, ttl_seconds=self.ttl_for(kind, ttl_seconds), source="cache_state"))
        ttl = int(ttl_seconds if ttl_seconds is not None else row["ttl_seconds"])
        created_at = float(row["created_at"])
        stale = time.time() - created_at > ttl
        state = "stale" if stale else "hit"
        if stale and not allow_stale:
            return CacheRead(None, self.status("miss", key=key, created_at=created_at, ttl_seconds=ttl, source=row["source"]))
        try:
            payload = json.loads(row["payload"])
        except Exception as exc:
            return CacheRead(None, self.status("error", key=key, created_at=created_at, ttl_seconds=ttl, source=row["source"], error=str(exc)))
        return CacheRead(payload, self.status(state, key=key, created_at=created_at, ttl_seconds=ttl, source=row["source"]))

    def latest(self, kind: str, *, symbol: str = "", allow_stale: bool = True, ttl_seconds: int | None = None) -> CacheRead:
        sql = "SELECT * FROM cache_state WHERE kind=?"
        params: list[Any] = [kind]
        if symbol:
            sql += " AND symbol=?"
            params.append(symbol)
        sql += " ORDER BY updated_at DESC LIMIT 1"
        with self._connect() as conn:
            row = conn.execute(sql, params).fetchone()
        if not row:
            return CacheRead(None, self.status("miss", ttl_seconds=self.ttl_for(kind, ttl_seconds), source="cache_state"))
        return self.get(kind, row["key"], allow_stale=allow_stale, ttl_seconds=ttl_seconds)

    def clear(self, kind: str | None = None, key: str | None = None, symbol: str | None = None) -> int:
        sql = "DELETE FROM cache_state"
        where = []
        params: list[Any] = []
        if kind:
            where.append("kind=?")
            params.append(kind)
        if key:
            where.append("key=?")
            params.append(key)
        if symbol:
            where.append("symbol=?")
            params.append(symbol)
        if where:
            sql += " WHERE " + " AND ".join(where)
        with self._connect() as conn:
            cur = conn.execute(sql, params)
            return int(cur.rowcount or 0)

    def overview(self) -> dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT kind, COUNT(*) AS count, MAX(updated_at) AS latest_updated, MIN(created_at) AS oldest_created
                FROM cache_state GROUP BY kind ORDER BY kind
                """
            ).fetchall()
        now = time.time()
        by_kind = {r["kind"]: r for r in rows}
        items = []
        all_kinds = list(DEFAULT_TTLS)
        for kind in sorted(set(all_kinds) | set(by_kind)):
            r = by_kind.get(kind)
            ttl = self.ttl_for(kind)
            if r:
                age = now - float(r["latest_updated"] or now)
                latest_updated = datetime.fromtimestamp(float(r["latest_updated"])).isoformat(timespec="seconds") if r["latest_updated"] else None
                oldest_created = datetime.fromtimestamp(float(r["oldest_created"])).isoformat(timespec="seconds") if r["oldest_created"] else None
                count = int(r["count"] or 0)
                status = "stale" if age > ttl else "hit"
            else:
                age = None
                latest_updated = None
                oldest_created = None
                count = 0
                status = "miss"
            items.append({
                "kind": kind,
                "count": count,
                "latest_updated": latest_updated,
                "oldest_created": oldest_created,
                "ttl_seconds": ttl,
                "latest_age_seconds": round(age, 2) if age is not None else None,
                "latest_status": status,
            })
        return {
            "ok": True,
            "db_path": str(self.db_path),
            "items": items,
            "default_ttls": DEFAULT_TTLS,
            "cache_status": self.status("hit" if rows else "miss", source="cache_state_overview"),
        }

    def save_screener_snapshot(self, snapshot_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.put("screener_snapshot", snapshot_id, payload, symbol="", source="screener_run")

    def get_screener_snapshot(self, snapshot_id: str) -> CacheRead:
        return self.get("screener_snapshot", snapshot_id, allow_stale=True)

    def latest_screener_snapshot(self) -> CacheRead:
        return self.latest("screener_snapshot", allow_stale=True)

    def save_info_snapshot(self, snapshot_id: str, symbol: str, payload: dict[str, Any], *, mode: str = "normal") -> dict[str, Any]:
        data = dict(payload or {})
        data.setdefault("mode", mode)
        return self.put("info_snapshot", snapshot_id, data, symbol=symbol, source=f"info_{mode}")

    def get_info_snapshot(self, snapshot_id: str) -> CacheRead:
        return self.get("info_snapshot", snapshot_id, allow_stale=True)

    def latest_info_snapshot(self, symbol: str) -> CacheRead:
        return self.latest("info_snapshot", symbol=symbol, allow_stale=True)

    def save_kline_cache(self, key: str, symbol: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.put("kline_cache", key, payload, symbol=symbol, source="kline_api")

    def get_kline_cache(self, key: str) -> CacheRead:
        return self.get("kline_cache", key, allow_stale=True)
