from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from quant_data.config import CACHE_DB
from quant_data.models import Asset, AssetType, Bar, Quote, IntradayPoint
from quant_data.utils import normalize_symbol, parse_dt


class MarketCache:
    """SQLite 本地缓存。

    作用：
    1. 降低公共接口访问频率；
    2. 外部接口短暂失败时仍可读取最近一次数据；
    3. 后续系统开发时，前端/策略/回测都可以从这里取数。
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
                CREATE TABLE IF NOT EXISTS quotes (
                    symbol TEXT PRIMARY KEY,
                    name TEXT,
                    ts TEXT,
                    last REAL,
                    pre_close REAL,
                    open REAL,
                    high REAL,
                    low REAL,
                    volume REAL,
                    amount REAL,
                    change REAL,
                    change_pct REAL,
                    turnover REAL,
                    amplitude REAL,
                    pe_dynamic REAL,
                    pb REAL,
                    volume_ratio REAL,
                    total_market_cap REAL,
                    float_market_cap REAL,
                    order_ratio REAL,
                    order_diff REAL,
                    market TEXT,
                    asset_type TEXT,
                    source TEXT
                )
                """
            )
            # 兼容旧版本数据库：如果已有 quotes 表但缺少新增字段，则自动补列。
            existing_cols = {r[1] for r in conn.execute("PRAGMA table_info(quotes)").fetchall()}
            extra_cols = {
                "volume_ratio": "REAL",
                "total_market_cap": "REAL",
                "float_market_cap": "REAL",
                "order_ratio": "REAL",
                "order_diff": "REAL",
            }
            for col, typ in extra_cols.items():
                if col not in existing_cols:
                    conn.execute(f"ALTER TABLE quotes ADD COLUMN {col} {typ}")

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bars (
                    symbol TEXT,
                    frame TEXT,
                    ts TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    amount REAL,
                    turnover REAL,
                    change_pct REAL,
                    source TEXT,
                    PRIMARY KEY(symbol, frame, ts)
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS intraday_points (
                    symbol TEXT,
                    trade_date TEXT,
                    ts TEXT,
                    price REAL,
                    avg_price REAL,
                    volume REAL,
                    amount REAL,
                    source TEXT,
                    PRIMARY KEY(symbol, trade_date, ts)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_intraday_symbol_date ON intraday_points(symbol, trade_date, ts)")

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS assets (
                    symbol TEXT PRIMARY KEY,
                    name TEXT,
                    asset_type TEXT,
                    market TEXT,
                    exchange TEXT,
                    source TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bars_symbol_frame_ts ON bars(symbol, frame, ts)")
            conn.commit()

    def save_quotes(self, quotes: Iterable[Quote]) -> None:
        rows = [q.to_dict() for q in quotes]
        if not rows:
            return
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO quotes (
                    symbol,name,ts,last,pre_close,open,high,low,volume,amount,change,change_pct,
                    turnover,amplitude,pe_dynamic,pb,volume_ratio,total_market_cap,float_market_cap,order_ratio,order_diff,market,asset_type,source
                ) VALUES (
                    :symbol,:name,:ts,:last,:pre_close,:open,:high,:low,:volume,:amount,:change,:change_pct,
                    :turnover,:amplitude,:pe_dynamic,:pb,:volume_ratio,:total_market_cap,:float_market_cap,:order_ratio,:order_diff,:market,:asset_type,:source
                )
                """,
                rows,
            )
            conn.commit()

    def get_quote(self, symbol: str, max_age_seconds: float | None = None) -> Quote | None:
        symbol = normalize_symbol(symbol)
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM quotes WHERE symbol=?", (symbol,)).fetchone()
        if not row:
            return None
        ts = parse_dt(row["ts"])
        if max_age_seconds is not None and datetime.now() - ts > timedelta(seconds=max_age_seconds):
            return None
        return Quote(
            symbol=row["symbol"],
            name=row["name"] or row["symbol"],
            ts=ts,
            last=row["last"] or 0.0,
            pre_close=row["pre_close"] or 0.0,
            open=row["open"] or 0.0,
            high=row["high"] or 0.0,
            low=row["low"] or 0.0,
            volume=row["volume"] or 0.0,
            amount=row["amount"] or 0.0,
            change=row["change"] or 0.0,
            change_pct=row["change_pct"] or 0.0,
            turnover=row["turnover"],
            amplitude=row["amplitude"],
            pe_dynamic=row["pe_dynamic"],
            pb=row["pb"],
            volume_ratio=row["volume_ratio"] if "volume_ratio" in row.keys() else None,
            total_market_cap=row["total_market_cap"] if "total_market_cap" in row.keys() else None,
            float_market_cap=row["float_market_cap"] if "float_market_cap" in row.keys() else None,
            order_ratio=row["order_ratio"] if "order_ratio" in row.keys() else None,
            order_diff=row["order_diff"] if "order_diff" in row.keys() else None,
            market=row["market"] or "CN",
            asset_type=AssetType(row["asset_type"] or "stock"),
            source=row["source"] or "cache",
        )

    def save_bars(self, bars: Iterable[Bar]) -> None:
        rows = [b.to_dict() for b in bars]
        if not rows:
            return
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO bars (
                    symbol,frame,ts,open,high,low,close,volume,amount,turnover,change_pct,source
                ) VALUES (
                    :symbol,:frame,:ts,:open,:high,:low,:close,:volume,:amount,:turnover,:change_pct,:source
                )
                """,
                rows,
            )
            conn.commit()

    def get_bars(self, symbol: str, frame: str, limit: int = 240, max_age_seconds: float | None = None) -> list[Bar]:
        symbol = normalize_symbol(symbol)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM bars
                WHERE symbol=? AND frame=?
                ORDER BY ts DESC
                LIMIT ?
                """,
                (symbol, frame, int(limit)),
            ).fetchall()
        if not rows:
            return []
        rows = list(reversed(rows))
        latest_ts = parse_dt(rows[-1]["ts"])
        if max_age_seconds is not None and datetime.now() - latest_ts > timedelta(seconds=max_age_seconds):
            # 对日线而言，ts 是交易日 00:00:00，不能直接用自然时间判断是否过期。
            if frame != "1d":
                return []
        bars: list[Bar] = []
        for row in rows:
            bars.append(
                Bar(
                    symbol=row["symbol"],
                    frame=row["frame"],
                    ts=parse_dt(row["ts"]),
                    open=row["open"] or 0.0,
                    high=row["high"] or 0.0,
                    low=row["low"] or 0.0,
                    close=row["close"] or 0.0,
                    volume=row["volume"] or 0.0,
                    amount=row["amount"] or 0.0,
                    turnover=row["turnover"],
                    change_pct=row["change_pct"],
                    source=row["source"] or "cache",
                )
            )
        return bars


    def save_intraday(self, points: Iterable[IntradayPoint]) -> None:
        rows = []
        for p in points:
            d = p.to_dict()
            d["trade_date"] = p.ts.date().isoformat()
            rows.append(d)
        if not rows:
            return
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO intraday_points (
                    symbol,trade_date,ts,price,avg_price,volume,amount,source
                ) VALUES (
                    :symbol,:trade_date,:ts,:price,:avg_price,:volume,:amount,:source
                )
                """,
                rows,
            )
            conn.commit()

    def get_intraday(self, symbol: str, trade_date: str | None = None, limit: int = 400) -> list[IntradayPoint]:
        symbol = normalize_symbol(symbol)
        with self._connect() as conn:
            if trade_date is None:
                row = conn.execute(
                    "SELECT trade_date FROM intraday_points WHERE symbol=? ORDER BY trade_date DESC LIMIT 1",
                    (symbol,),
                ).fetchone()
                if not row:
                    return []
                trade_date = row["trade_date"]
            rows = conn.execute(
                """
                SELECT * FROM intraday_points
                WHERE symbol=? AND trade_date=?
                ORDER BY ts ASC
                LIMIT ?
                """,
                (symbol, trade_date, int(limit)),
            ).fetchall()
        out: list[IntradayPoint] = []
        for row in rows:
            out.append(
                IntradayPoint(
                    symbol=row["symbol"],
                    ts=parse_dt(row["ts"]),
                    price=row["price"] or 0.0,
                    avg_price=row["avg_price"],
                    volume=row["volume"],
                    amount=row["amount"],
                    source=row["source"] or "cache",
                )
            )
        return out

    def save_assets(self, assets: Iterable[Asset]) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        rows = []
        for a in assets:
            data = a.to_dict()
            data["updated_at"] = now
            rows.append(data)
        if not rows:
            return
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO assets(symbol,name,asset_type,market,exchange,source,updated_at)
                VALUES(:symbol,:name,:asset_type,:market,:exchange,:source,:updated_at)
                """,
                rows,
            )
            conn.commit()

    def search_assets(self, keyword: str, limit: int = 30) -> list[Asset]:
        kw = f"%{keyword.strip()}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM assets
                WHERE symbol LIKE ? OR name LIKE ?
                ORDER BY symbol
                LIMIT ?
                """,
                (kw, kw, int(limit)),
            ).fetchall()
        return [
            Asset(
                symbol=r["symbol"],
                name=r["name"],
                asset_type=AssetType(r["asset_type"] or "stock"),
                market=r["market"] or "CN",
                exchange=r["exchange"] or "",
                source=r["source"] or "cache",
            )
            for r in rows
        ]

    def stats(self) -> dict:
        with self._connect() as conn:
            q = conn.execute("SELECT COUNT(*) AS c FROM quotes").fetchone()["c"]
            b = conn.execute("SELECT COUNT(*) AS c FROM bars").fetchone()["c"]
            a = conn.execute("SELECT COUNT(*) AS c FROM assets").fetchone()["c"]
            t = conn.execute("SELECT COUNT(*) AS c FROM intraday_points").fetchone()["c"]
        return {"db_path": str(self.db_path), "quotes": q, "bars": b, "intraday_points": t, "assets": a}
