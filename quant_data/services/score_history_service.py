from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

from quant_data.config import CACHE_DB
from quant_data.utils import normalize_symbol


class ScoreHistoryService:
    """股票筛选评分历史。

    以“交易日/自然日 + 股票代码”为主键保存评分，因此同一天重复筛选会更新当天记录。
    这样可以满足“评分按天更新、可查看趋势”的需求，并避免高频刷新生成大量重复记录。
    """

    def __init__(self, db_path: str | Path = CACHE_DB) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS screener_scores (
                    score_date TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    name TEXT,
                    asset_type TEXT,
                    total_score REAL,
                    low_score REAL,
                    trend_score REAL,
                    volume_score REAL,
                    value_score REAL,
                    risk_penalty REAL,
                    grade TEXT,
                    last REAL,
                    change_pct REAL,
                    amount REAL,
                    tags_json TEXT,
                    risks_json TEXT,
                    reason TEXT,
                    mode TEXT,
                    snapshot_json TEXT,
                    updated_at TEXT,
                    PRIMARY KEY(score_date, symbol)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_scores_symbol_date ON screener_scores(symbol, score_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_scores_date_score ON screener_scores(score_date, total_score DESC)")
            conn.commit()

    def save_results(self, results: Iterable[dict], mode: str = "balanced", score_date: str | None = None) -> int:
        rows = []
        d = score_date or date.today().isoformat()
        now = datetime.now().isoformat(timespec="seconds")
        for r in results or []:
            try:
                symbol = normalize_symbol(r.get("symbol") or "")
            except Exception:
                continue
            if not symbol:
                continue
            rows.append(
                {
                    "score_date": d,
                    "symbol": symbol,
                    "name": r.get("name") or symbol,
                    "asset_type": r.get("asset_type"),
                    "total_score": r.get("total_score"),
                    "low_score": r.get("low_score"),
                    "trend_score": r.get("trend_score"),
                    "volume_score": r.get("volume_score"),
                    "value_score": r.get("value_score"),
                    "risk_penalty": r.get("risk_penalty"),
                    "grade": r.get("grade"),
                    "last": r.get("last"),
                    "change_pct": r.get("change_pct"),
                    "amount": r.get("amount"),
                    "tags_json": json.dumps(r.get("tags") or [], ensure_ascii=False),
                    "risks_json": json.dumps(r.get("risk_flags") or [], ensure_ascii=False),
                    "reason": r.get("reason") or "",
                    "mode": mode,
                    "snapshot_json": json.dumps(r, ensure_ascii=False),
                    "updated_at": now,
                }
            )
        if not rows:
            return 0
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO screener_scores (
                    score_date,symbol,name,asset_type,total_score,low_score,trend_score,volume_score,value_score,risk_penalty,
                    grade,last,change_pct,amount,tags_json,risks_json,reason,mode,snapshot_json,updated_at
                ) VALUES (
                    :score_date,:symbol,:name,:asset_type,:total_score,:low_score,:trend_score,:volume_score,:value_score,:risk_penalty,
                    :grade,:last,:change_pct,:amount,:tags_json,:risks_json,:reason,:mode,:snapshot_json,:updated_at
                )
                """,
                rows,
            )
            conn.commit()
        return len(rows)

    def history(self, symbol: str, days: int = 90) -> list[dict]:
        symbol = normalize_symbol(symbol)
        days = max(1, min(int(days or 90), 1000))
        start = (date.today() - timedelta(days=days)).isoformat()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM screener_scores
                WHERE symbol=? AND score_date>=?
                ORDER BY score_date ASC
                """,
                (symbol, start),
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def latest(self, limit: int = 100, score_date: str | None = None) -> list[dict]:
        limit = max(1, min(int(limit or 100), 1000))
        with self._connect() as conn:
            if score_date:
                rows = conn.execute(
                    "SELECT * FROM screener_scores WHERE score_date=? ORDER BY total_score DESC LIMIT ?",
                    (score_date, limit),
                ).fetchall()
            else:
                drow = conn.execute("SELECT MAX(score_date) AS d FROM screener_scores").fetchone()
                d = drow["d"] if drow else None
                rows = conn.execute(
                    "SELECT * FROM screener_scores WHERE score_date=? ORDER BY total_score DESC LIMIT ?",
                    (d, limit),
                ).fetchall() if d else []
        return [self._row_to_dict(r) for r in rows]

    def _row_to_dict(self, r: sqlite3.Row) -> dict:
        def load_json(s, default):
            try:
                return json.loads(s) if s else default
            except Exception:
                return default
        return {
            "score_date": r["score_date"],
            "symbol": r["symbol"],
            "name": r["name"],
            "asset_type": r["asset_type"],
            "total_score": r["total_score"],
            "low_score": r["low_score"],
            "trend_score": r["trend_score"],
            "volume_score": r["volume_score"],
            "value_score": r["value_score"],
            "risk_penalty": r["risk_penalty"],
            "grade": r["grade"],
            "last": r["last"],
            "change_pct": r["change_pct"],
            "amount": r["amount"],
            "tags": load_json(r["tags_json"], []),
            "risk_flags": load_json(r["risks_json"], []),
            "reason": r["reason"],
            "mode": r["mode"],
            "snapshot": load_json(r["snapshot_json"], {}),
            "updated_at": r["updated_at"],
        }
