from __future__ import annotations
import json, sqlite3
from pathlib import Path
from datetime import datetime

class FeatureStoreService:
    def __init__(self, path: str | Path = "data/feature_store.sqlite") -> None:
        self.path=Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()
    def _init(self):
        with sqlite3.connect(self.path) as con:
            con.execute("""CREATE TABLE IF NOT EXISTS features(symbol TEXT, namespace TEXT, ts TEXT, data TEXT, quality_score REAL, PRIMARY KEY(symbol, namespace, ts))""")
    def put(self, symbol: str, namespace: str, data: dict, quality_score: float | None=None) -> dict:
        ts=datetime.now().isoformat(timespec='seconds')
        with sqlite3.connect(self.path) as con:
            con.execute("INSERT OR REPLACE INTO features VALUES(?,?,?,?,?)",(symbol,namespace,ts,json.dumps(data,ensure_ascii=False),quality_score))
        return {"symbol":symbol,"namespace":namespace,"ts":ts,"quality_score":quality_score}
    def latest(self, symbol: str, namespace: str) -> dict | None:
        with sqlite3.connect(self.path) as con:
            row=con.execute("SELECT ts,data,quality_score FROM features WHERE symbol=? AND namespace=? ORDER BY ts DESC LIMIT 1",(symbol,namespace)).fetchone()
        if not row: return None
        return {"symbol":symbol,"namespace":namespace,"ts":row[0],"data":json.loads(row[1]),"quality_score":row[2]}
