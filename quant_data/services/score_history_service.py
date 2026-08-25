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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_score_snapshots (
                    score_date TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    name TEXT,
                    mode TEXT NOT NULL,
                    strategy_family TEXT NOT NULL,
                    final_score REAL,
                    screening_score REAL,
                    daily_k_score REAL,
                    intraday_score REAL,
                    fundamental_score REAL,
                    technical_score REAL,
                    information_score REAL,
                    fund_flow_score REAL,
                    market_score REAL,
                    anomaly_score REAL,
                    action TEXT,
                    quality_status TEXT,
                    auto_entry_eligible INTEGER NOT NULL DEFAULT 0,
                    provenance_id TEXT,
                    source TEXT,
                    snapshot_json TEXT,
                    updated_at TEXT,
                    PRIMARY KEY(score_date, symbol, mode, strategy_family)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_daily_scores_symbol_date "
                "ON daily_score_snapshots(symbol, score_date, updated_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_daily_scores_date_score "
                "ON daily_score_snapshots(score_date, final_score DESC)"
            )
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

    def save_daily_snapshots(
        self,
        snapshots: Iterable[dict],
        *,
        score_date: str | None = None,
    ) -> int:
        rows: list[dict] = []
        default_date = score_date or date.today().isoformat()
        now = datetime.now().isoformat(timespec="seconds")
        for snapshot in snapshots or []:
            if not isinstance(snapshot, dict):
                continue
            try:
                symbol = normalize_symbol(snapshot.get("symbol") or "")
            except Exception:
                continue
            if not symbol:
                continue
            rows.append(
                {
                    "score_date": str(snapshot.get("score_date") or default_date),
                    "symbol": symbol,
                    "name": snapshot.get("name") or symbol,
                    "mode": str(snapshot.get("mode") or "daily_monitor"),
                    "strategy_family": str(snapshot.get("strategy_family") or "swing"),
                    "final_score": snapshot.get("final_score"),
                    "screening_score": snapshot.get("screening_score"),
                    "daily_k_score": snapshot.get("daily_k_score"),
                    "intraday_score": snapshot.get("intraday_score"),
                    "fundamental_score": snapshot.get("fundamental_score"),
                    "technical_score": snapshot.get("technical_score"),
                    "information_score": snapshot.get("information_score"),
                    "fund_flow_score": snapshot.get("fund_flow_score"),
                    "market_score": snapshot.get("market_score"),
                    "anomaly_score": snapshot.get("anomaly_score"),
                    "action": snapshot.get("action") or "数据不足",
                    "quality_status": snapshot.get("quality_status") or "missing",
                    "auto_entry_eligible": 1 if snapshot.get("auto_entry_eligible") else 0,
                    "provenance_id": snapshot.get("provenance_id") or "",
                    "source": snapshot.get("source") or "daily_score_scheduler",
                    "snapshot_json": json.dumps(snapshot, ensure_ascii=False),
                    "updated_at": str(snapshot.get("updated_at") or now),
                }
            )
        if not rows:
            return 0
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO daily_score_snapshots (
                    score_date,symbol,name,mode,strategy_family,final_score,screening_score,daily_k_score,
                    intraday_score,fundamental_score,technical_score,information_score,fund_flow_score,
                    market_score,anomaly_score,action,quality_status,auto_entry_eligible,provenance_id,
                    source,snapshot_json,updated_at
                ) VALUES (
                    :score_date,:symbol,:name,:mode,:strategy_family,:final_score,:screening_score,:daily_k_score,
                    :intraday_score,:fundamental_score,:technical_score,:information_score,:fund_flow_score,
                    :market_score,:anomaly_score,:action,:quality_status,:auto_entry_eligible,:provenance_id,
                    :source,:snapshot_json,:updated_at
                )
                """,
                rows,
            )
            conn.commit()
        return len(rows)

    def daily_history(self, symbol: str, *, days: int = 90, mode: str = "") -> list[dict]:
        symbol = normalize_symbol(symbol)
        days = max(1, min(int(days or 90), 1000))
        start = (date.today() - timedelta(days=days)).isoformat()
        with self._connect() as conn:
            if mode and mode != "all":
                rows = conn.execute(
                    """
                    SELECT * FROM daily_score_snapshots
                    WHERE symbol=? AND score_date>=? AND mode=?
                    ORDER BY score_date ASC, updated_at ASC
                    """,
                    (symbol, start, mode),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM daily_score_snapshots
                    WHERE symbol=? AND score_date>=?
                    ORDER BY score_date ASC, updated_at ASC
                    """,
                    (symbol, start),
                ).fetchall()
        return [self._daily_row_to_dict(row) for row in rows]

    def daily_latest(self, *, limit: int = 100, score_date: str | None = None) -> list[dict]:
        limit = max(1, min(int(limit or 100), 1000))
        with self._connect() as conn:
            selected_date = score_date
            if not selected_date:
                row = conn.execute("SELECT MAX(score_date) AS d FROM daily_score_snapshots").fetchone()
                selected_date = row["d"] if row else None
            rows = (
                conn.execute(
                    """
                    SELECT * FROM daily_score_snapshots
                    WHERE score_date=?
                    ORDER BY final_score DESC, symbol ASC LIMIT ?
                    """,
                    (selected_date, limit),
                ).fetchall()
                if selected_date
                else []
            )
        return [self._daily_row_to_dict(row) for row in rows]

    def daily_status(self) -> dict:
        today = date.today().isoformat()
        with self._connect() as conn:
            summary = conn.execute(
                """
                SELECT COUNT(*) AS total, COUNT(DISTINCT symbol) AS symbols,
                       MAX(score_date) AS latest_date, MAX(updated_at) AS latest_at
                FROM daily_score_snapshots
                """
            ).fetchone()
            today_row = conn.execute(
                "SELECT COUNT(*) AS total, COUNT(DISTINCT symbol) AS symbols "
                "FROM daily_score_snapshots WHERE score_date=?",
                (today,),
            ).fetchone()
        return {
            "total_snapshots": int(summary["total"] if summary else 0),
            "symbol_count": int(summary["symbols"] if summary else 0),
            "latest_score_date": summary["latest_date"] if summary else None,
            "latest_updated_at": summary["latest_at"] if summary else None,
            "today": today,
            "today_snapshots": int(today_row["total"] if today_row else 0),
            "today_symbols": int(today_row["symbols"] if today_row else 0),
        }

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

    def _daily_row_to_dict(self, r: sqlite3.Row) -> dict:
        try:
            snapshot = json.loads(r["snapshot_json"]) if r["snapshot_json"] else {}
        except Exception:
            snapshot = {}
        return {
            "score_date": r["score_date"],
            "symbol": r["symbol"],
            "name": r["name"],
            "mode": r["mode"],
            "strategy_family": r["strategy_family"],
            "final_score": r["final_score"],
            "screening_score": r["screening_score"],
            "daily_k_score": r["daily_k_score"],
            "intraday_score": r["intraday_score"],
            "fundamental_score": r["fundamental_score"],
            "technical_score": r["technical_score"],
            "information_score": r["information_score"],
            "fund_flow_score": r["fund_flow_score"],
            "market_score": r["market_score"],
            "anomaly_score": r["anomaly_score"],
            "action": r["action"],
            "quality_status": r["quality_status"],
            "auto_entry_eligible": bool(r["auto_entry_eligible"]),
            "provenance_id": r["provenance_id"],
            "source": r["source"],
            "snapshot": snapshot,
            "updated_at": r["updated_at"],
        }
