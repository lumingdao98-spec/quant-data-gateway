from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from quant_data.config import DATA_DIR
from quant_data.utils import normalize_symbol


class WatchlistService:
    """服务端实时监测列表。

    说明：
    - 前端 localStorage 只能在当前浏览器里保存；
    - 服务端 watchlist.json 作为统一监测列表，筛选页和行情页都能读取；
    - 后续接入桌面端、策略任务、自动交易时都可以复用这个列表。
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else Path(DATA_DIR) / "watchlist.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"symbols": ["300750", "600519", "000001", "159915", "510300"], "updated_at": datetime.now().isoformat(timespec="seconds")})

    def _read(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"symbols": [], "updated_at": None}

    def _write(self, data: dict) -> None:
        data["symbols"] = self._clean(data.get("symbols", []))
        data["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _clean(self, symbols) -> list[str]:
        out: list[str] = []
        for s in symbols or []:
            try:
                sym = normalize_symbol(str(s).strip())
            except Exception:
                continue
            if sym and sym not in out:
                out.append(sym)
        return out

    def list(self) -> dict:
        data = self._read()
        symbols = self._clean(data.get("symbols", []))
        if symbols != data.get("symbols", []):
            data["symbols"] = symbols
            self._write(data)
        return {"symbols": symbols, "updated_at": data.get("updated_at"), "count": len(symbols), "path": str(self.path)}

    def set(self, symbols) -> dict:
        data = {"symbols": self._clean(symbols)}
        self._write(data)
        return self.list()

    def add(self, symbols) -> dict:
        data = self._read()
        old = self._clean(data.get("symbols", []))
        for sym in self._clean(symbols):
            if sym not in old:
                old.append(sym)
        return self.set(old)

    def remove(self, symbols) -> dict:
        remove_set = set(self._clean(symbols))
        old = self._clean(self._read().get("symbols", []))
        return self.set([s for s in old if s not in remove_set])
