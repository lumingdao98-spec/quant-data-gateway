from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from quant_data.utils import normalize_symbol
from quant_data.services.news_cleaner import is_page_chrome_summary, valid_news_item


class NewsStoreService:
    """持久化中文新闻、公告、信息面分析结果。

    设计目标：
    1. 信息面可复用，避免每次筛选都重复抓取；
    2. 近期信息和历史风险信息都能保留；
    3. 原始条目、来源、日期、评分依据可追溯。
    """

    def __init__(self, db_path: str | Path = "data/news_store.sqlite") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS news_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                name TEXT,
                title TEXT NOT NULL,
                url TEXT,
                source TEXT,
                source_type TEXT,
                category TEXT,
                published_at TEXT,
                published_at_norm TEXT,
                publish_time TEXT,
                event_time TEXT,
                crawl_time TEXT,
                time_confidence TEXT,
                time_basis TEXT,
                event_type TEXT,
                issuer TEXT,
                period TEXT,
                document_id TEXT,
                summary TEXT,
                relevance_score REAL,
                sentiment_score REAL,
                credibility_score REAL,
                impact_score REAL,
                fake_risk_score REAL,
                duplicate_group TEXT,
                event_key TEXT,
                raw_json TEXT,
                first_seen_at INTEGER NOT NULL,
                last_seen_at INTEGER NOT NULL,
                UNIQUE(symbol, duplicate_group)
            )
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS news_analysis (
                symbol TEXT NOT NULL,
                name TEXT,
                analysis_key TEXT NOT NULL,
                result_json TEXT NOT NULL,
                saved_at INTEGER NOT NULL,
                PRIMARY KEY(symbol, analysis_key)
            )
            """)
            cols = {row[1] for row in conn.execute("PRAGMA table_info(news_items)").fetchall()}
            for col in ["publish_time", "event_time", "crawl_time", "time_confidence", "time_basis", "event_type", "issuer", "period", "document_id", "event_key"]:
                if col not in cols:
                    conn.execute(f"ALTER TABLE news_items ADD COLUMN {col} TEXT")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_symbol_date ON news_items(symbol, published_at_norm)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_symbol_seen ON news_items(symbol, last_seen_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_symbol_event ON news_items(symbol, event_type, event_time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_symbol_event_key ON news_items(symbol, event_key)")

    def save_analysis(self, symbol: str, key: str, result: dict[str, Any], name: str | None = None) -> None:
        symbol = normalize_symbol(symbol)
        with self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO news_analysis(symbol,name,analysis_key,result_json,saved_at)
                VALUES(?,?,?,?,?)""",
                (symbol, name or "", key, json.dumps(result, ensure_ascii=False), int(time.time())),
            )

    def read_analysis(self, symbol: str, key: str, ttl_seconds: int) -> dict[str, Any] | None:
        symbol = normalize_symbol(symbol)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT result_json,saved_at FROM news_analysis WHERE symbol=? AND analysis_key=?",
                (symbol, key),
            ).fetchone()
        if not row:
            return None
        if time.time() - float(row["saved_at"] or 0) > ttl_seconds:
            return None
        try:
            data = json.loads(row["result_json"])
            if isinstance(data, dict):
                data.setdefault("cache_info", {})
                data["cache_info"].update({"hit": True, "store": "sqlite", "saved_at_ts": row["saved_at"]})
                return data
        except Exception:
            return None
        return None

    def upsert_items(self, symbol: str, name: str | None, items: list[Any]) -> int:
        symbol = normalize_symbol(symbol)
        now = int(time.time())
        n = 0
        with self._connect() as conn:
            for item in items:
                if hasattr(item, "to_dict"):
                    d = item.to_dict()
                elif isinstance(item, dict):
                    d = dict(item)
                else:
                    continue
                title = str(d.get("title") or "").strip()
                summary = str(d.get("summary") or "")
                source = str(d.get("source") or "")
                source_type = str(d.get("source_type") or "news")
                ok, _reason = valid_news_item(
                    title, summary, source=source, url=str(d.get("url") or ""), symbol=symbol, name=name or "",
                    source_type=source_type, base_relevant=float(d.get("relevance_score") or 0) >= 20,
                    allow_macro=source_type in {"macro", "policy", "global"},
                )
                if not ok:
                    continue
                event_key = str(d.get("event_key") or d.get("duplicate_group") or "").strip()
                if not event_key:
                    event_key = "text:" + hashlib.sha1(f"{title}|{d.get('url') or ''}".encode("utf-8", "ignore")).hexdigest()[:16]
                # 存储唯一键必须以 event_key 优先，避免旧 duplicate_group 不一致导致同一公告重复展示。
                duplicate_group = event_key
                d["duplicate_group"] = duplicate_group
                d["event_key"] = event_key
                raw_json = json.dumps(d, ensure_ascii=False)
                conn.execute(
                    """INSERT INTO news_items(
                        symbol,name,title,url,source,source_type,category,published_at,published_at_norm,
                        publish_time,event_time,crawl_time,time_confidence,time_basis,event_type,issuer,period,document_id,summary,
                        relevance_score,sentiment_score,credibility_score,impact_score,fake_risk_score,duplicate_group,event_key,raw_json,first_seen_at,last_seen_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(symbol,duplicate_group) DO UPDATE SET
                        name=excluded.name,
                        title=excluded.title,
                        url=excluded.url,
                        source=excluded.source,
                        source_type=excluded.source_type,
                        category=excluded.category,
                        published_at=excluded.published_at,
                        published_at_norm=excluded.published_at_norm,
                        publish_time=excluded.publish_time,
                        event_time=excluded.event_time,
                        crawl_time=excluded.crawl_time,
                        time_confidence=excluded.time_confidence,
                        time_basis=excluded.time_basis,
                        event_type=excluded.event_type,
                        issuer=excluded.issuer,
                        period=excluded.period,
                        document_id=excluded.document_id,
                        summary=CASE WHEN length(excluded.summary)>length(news_items.summary) THEN excluded.summary ELSE news_items.summary END,
                        relevance_score=excluded.relevance_score,
                        sentiment_score=excluded.sentiment_score,
                        credibility_score=excluded.credibility_score,
                        impact_score=excluded.impact_score,
                        fake_risk_score=excluded.fake_risk_score,
                        event_key=excluded.event_key,
                        raw_json=excluded.raw_json,
                        last_seen_at=excluded.last_seen_at""",
                    (
                        symbol, name or "", title, d.get("url") or "", source, source_type, d.get("category") or "其他信息",
                        d.get("published_at") or "", d.get("published_at_norm") or "",
                        d.get("publish_time") or "", d.get("event_time") or "", d.get("crawl_time") or "",
                        d.get("time_confidence") or "", d.get("time_basis") or "", d.get("event_type") or "",
                        d.get("issuer") or name or "", d.get("period") or "", d.get("document_id") or "", d.get("summary") or "",
                        d.get("relevance_score"), d.get("sentiment_score"), d.get("credibility_score"), d.get("impact_score"), d.get("fake_risk_score"),
                        duplicate_group, event_key, raw_json, now, now,
                    ),
                )
                n += 1
            self._cleanup_symbol_duplicates(conn, symbol)
        return n


    def _row_event_key(self, d: dict[str, Any]) -> str:
        try:
            raw = json.loads(d.get("raw_json") or "{}")
            if isinstance(raw, dict):
                return str(raw.get("event_key") or raw.get("duplicate_group") or d.get("event_key") or d.get("duplicate_group") or "")
        except Exception:
            pass
        return str(d.get("event_key") or d.get("duplicate_group") or "")

    def _cleanup_symbol_duplicates(self, conn: sqlite3.Connection, symbol: str) -> None:
        """清理旧库中同一 event_key 但 duplicate_group 不同的历史重复行。"""
        rows = conn.execute("SELECT id,title,source,source_type,credibility_score,impact_score,last_seen_at,event_key,duplicate_group,raw_json FROM news_items WHERE symbol=?", (symbol,)).fetchall()
        groups: dict[str, list[sqlite3.Row]] = {}
        for r in rows:
            d = dict(r)
            key = self._row_event_key(d)
            if not key:
                continue
            groups.setdefault(key, []).append(r)
        for key, arr in groups.items():
            if len(arr) <= 1:
                continue
            def score(row: sqlite3.Row) -> tuple:
                d = dict(row)
                official = 1 if d.get("source_type") == "announcement" or float(d.get("credibility_score") or 0) >= 85 else 0
                return (official, float(d.get("credibility_score") or 0), float(d.get("impact_score") or 0), int(d.get("last_seen_at") or 0))
            keep = max(arr, key=score)
            drop_ids = [int(r["id"]) for r in arr if int(r["id"]) != int(keep["id"])]
            if drop_ids:
                conn.executemany("DELETE FROM news_items WHERE id=?", [(i,) for i in drop_ids])
                conn.execute("UPDATE news_items SET duplicate_group=?, event_key=? WHERE id=?", (key, key, int(keep["id"])))

    def _dedupe_output_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        out: list[dict[str, Any]] = []
        for d in rows:
            key = self._row_event_key(d) or str(d.get("duplicate_group") or d.get("title") or "")
            if key in seen:
                continue
            seen.add(key)
            out.append(d)
        return out

    def list_items(self, symbol: str, limit: int = 80, include_history_days: int | None = None) -> list[dict[str, Any]]:
        symbol = normalize_symbol(symbol)
        limit = max(1, min(int(limit or 80), 500))
        where = "symbol=?"
        args: list[Any] = [symbol]
        if include_history_days and include_history_days > 0:
            cutoff = int(time.time()) - int(include_history_days) * 86400
            # 有日期的按日期保留；无日期但最近见过的也保留，方便搜索页缺日期的条目不被直接丢掉。
            where += " AND (last_seen_at>=? OR published_at_norm='')"
            args.append(cutoff)
        with self._connect() as conn:
            rows = conn.execute(
                f"""SELECT * FROM news_items WHERE {where}
                ORDER BY
                  CASE WHEN published_at_norm='' THEN 1 ELSE 0 END,
                  published_at_norm DESC,
                  last_seen_at DESC
                LIMIT ?""",
                (*args, limit),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            try:
                raw = json.loads(d.get("raw_json") or "{}")
                if isinstance(raw, dict):
                    raw.update({k: d.get(k) for k in ["published_at_norm", "publish_time", "event_time", "crawl_time", "time_confidence", "time_basis", "event_type", "issuer", "period", "document_id", "event_key", "title", "url", "source", "source_type", "category", "summary"]})
                    if is_page_chrome_summary(raw.get("summary")):
                        raw["summary"] = ""
                        raw["content_loaded"] = False
                        raw["content_quality_status"] = "boilerplate_rejected"
                        raw["content_missing_reason"] = "缓存正文仅包含网页导航或免责声明，已拒绝参与正文评分"
                    ok, _reason = valid_news_item(str(raw.get("title") or ""), str(raw.get("summary") or ""), source=str(raw.get("source") or ""), url=str(raw.get("url") or ""), symbol=symbol, name=str(raw.get("name") or ""), source_type=str(raw.get("source_type") or "news"), base_relevant=float(raw.get("relevance_score") or 0) >= 20, allow_macro=str(raw.get("source_type") or "") in {"macro", "policy", "global"})
                    if ok:
                        out.append(raw)
                    continue
            except Exception:
                pass
            ok, _reason = valid_news_item(str(d.get("title") or ""), str(d.get("summary") or ""), source=str(d.get("source") or ""), url=str(d.get("url") or ""), symbol=symbol, name=str(d.get("name") or ""), source_type=str(d.get("source_type") or "news"), base_relevant=float(d.get("relevance_score") or 0) >= 20, allow_macro=str(d.get("source_type") or "") in {"macro", "policy", "global"})
            if ok:
                out.append(d)
        return self._dedupe_output_rows(out)


    def list_items_paged(
        self,
        symbol: str,
        page: int = 1,
        page_size: int = 30,
        include_history_days: int | None = None,
        sort: str = "desc",
        category: str | None = None,
        source: str | None = None,
        include_unknown_date: bool = True,
    ) -> dict[str, Any]:
        """分页读取信息面明细，支持时间顺序、分类/来源过滤和未知日期控制。"""
        symbol = normalize_symbol(symbol)
        page = max(1, int(page or 1))
        page_size = max(5, min(int(page_size or 30), 200))
        where = ["symbol=?"]
        args: list[Any] = [symbol]
        if include_history_days and include_history_days > 0:
            cutoff = int(time.time()) - int(include_history_days) * 86400
            where.append("(last_seen_at>=? OR published_at_norm='')")
            args.append(cutoff)
        if category:
            where.append("category=?")
            args.append(category)
        if source:
            where.append("source=?")
            args.append(source)
        if not include_unknown_date:
            where.append("published_at_norm<>''")
        where_sql = " AND ".join(where)
        order = "ASC" if str(sort).lower() == "asc" else "DESC"
        offset = (page - 1) * page_size
        with self._connect() as conn:
            total_row = conn.execute(f"SELECT COUNT(*) c FROM news_items WHERE {where_sql}", args).fetchone()
            rows = conn.execute(
                f"""SELECT * FROM news_items WHERE {where_sql}
                ORDER BY
                  CASE WHEN published_at_norm='' THEN 1 ELSE 0 END,
                  published_at_norm {order},
                  last_seen_at {order}
                LIMIT ? OFFSET ?""",
                (*args, page_size, offset),
            ).fetchall()
            # 统计尽量基于当前 symbol 全量，方便用户看信息结构占比。
            by_cat = conn.execute("SELECT category, COUNT(*) c FROM news_items WHERE symbol=? GROUP BY category ORDER BY c DESC", (symbol,)).fetchall()
            by_source = conn.execute("SELECT source, COUNT(*) c FROM news_items WHERE symbol=? GROUP BY source ORDER BY c DESC", (symbol,)).fetchall()
            by_date = conn.execute("""SELECT
                SUM(CASE WHEN published_at_norm='' THEN 1 ELSE 0 END) AS unknown_date,
                SUM(CASE WHEN published_at_norm<>'' THEN 1 ELSE 0 END) AS known_date,
                COUNT(*) AS total
                FROM news_items WHERE symbol=?""", (symbol,)).fetchone()
            dup = conn.execute("""SELECT COALESCE(NULLIF(event_key,''), duplicate_group) AS duplicate_group, COUNT(*) c, MAX(title) title
                FROM news_items WHERE symbol=? GROUP BY COALESCE(NULLIF(event_key,''), duplicate_group) HAVING COUNT(*)>1
                ORDER BY c DESC LIMIT 20""", (symbol,)).fetchall()
        data = []
        for r in rows:
            d = dict(r)
            try:
                raw = json.loads(d.get("raw_json") or "{}")
                if isinstance(raw, dict):
                    raw.update({k: d.get(k) for k in ["published_at_norm", "publish_time", "event_time", "crawl_time", "time_confidence", "time_basis", "event_type", "issuer", "period", "document_id", "event_key", "title", "url", "source", "source_type", "category", "summary", "duplicate_group", "first_seen_at", "last_seen_at"]})
                    if is_page_chrome_summary(raw.get("summary")):
                        raw["summary"] = ""
                        raw["content_loaded"] = False
                        raw["content_quality_status"] = "boilerplate_rejected"
                        raw["content_missing_reason"] = "缓存正文仅包含网页导航或免责声明，已拒绝参与正文评分"
                    ok, _reason = valid_news_item(str(raw.get("title") or ""), str(raw.get("summary") or ""), source=str(raw.get("source") or ""), url=str(raw.get("url") or ""), symbol=symbol, name=str(raw.get("name") or ""), source_type=str(raw.get("source_type") or "news"), base_relevant=float(raw.get("relevance_score") or 0) >= 20, allow_macro=str(raw.get("source_type") or "") in {"macro", "policy", "global"})
                    if ok:
                        data.append(raw)
                    continue
            except Exception:
                pass
            ok, _reason = valid_news_item(str(d.get("title") or ""), str(d.get("summary") or ""), source=str(d.get("source") or ""), url=str(d.get("url") or ""), symbol=symbol, name=str(d.get("name") or ""), source_type=str(d.get("source_type") or "news"), base_relevant=float(d.get("relevance_score") or 0) >= 20, allow_macro=str(d.get("source_type") or "") in {"macro", "policy", "global"})
            if ok:
                data.append(d)
        data = self._dedupe_output_rows(data)
        total = len(data) if data else int(total_row["c"] or 0) if total_row else 0
        return {
            "symbol": symbol,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size if page_size else 0,
            "data": data,
            "filters": {"category": category, "source": source, "sort": sort, "include_unknown_date": include_unknown_date, "history_days": include_history_days},
            "stats": {
                "by_category": [dict(x) for x in by_cat],
                "by_source": [dict(x) for x in by_source],
                "date_known": int((dict(by_date).get("known_date") if by_date else 0) or 0),
                "date_unknown": int((dict(by_date).get("unknown_date") if by_date else 0) or 0),
                "total": int((dict(by_date).get("total") if by_date else 0) or 0),
                "duplicate_groups": [dict(x) for x in dup],
            },
        }

    def stats(self, symbol: str | None = None) -> dict[str, Any]:
        with self._connect() as conn:
            if symbol:
                symbol = normalize_symbol(symbol)
                row = conn.execute("SELECT COUNT(*) AS c, MIN(first_seen_at) AS first_seen, MAX(last_seen_at) AS last_seen FROM news_items WHERE symbol=?", (symbol,)).fetchone()
                by_source = conn.execute("SELECT source, COUNT(*) c FROM news_items WHERE symbol=? GROUP BY source ORDER BY c DESC LIMIT 12", (symbol,)).fetchall()
                by_cat = conn.execute("SELECT category, COUNT(*) c FROM news_items WHERE symbol=? GROUP BY category ORDER BY c DESC LIMIT 12", (symbol,)).fetchall()
            else:
                row = conn.execute("SELECT COUNT(*) AS c, MIN(first_seen_at) AS first_seen, MAX(last_seen_at) AS last_seen FROM news_items").fetchone()
                by_source = conn.execute("SELECT source, COUNT(*) c FROM news_items GROUP BY source ORDER BY c DESC LIMIT 12").fetchall()
                by_cat = conn.execute("SELECT category, COUNT(*) c FROM news_items GROUP BY category ORDER BY c DESC LIMIT 12").fetchall()
        return {
            "db_path": str(self.db_path),
            "count": int(row["c"] or 0) if row else 0,
            "first_seen_ts": row["first_seen"] if row else None,
            "last_seen_ts": row["last_seen"] if row else None,
            "by_source": [dict(x) for x in by_source],
            "by_category": [dict(x) for x in by_cat],
            "note": "news_items 为持久化中文信息库，可复用历史公告/新闻；news_analysis 为短期分析缓存。",
        }
