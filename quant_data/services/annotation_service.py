from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any

from quant_data.utils import normalize_symbol


class AnnotationService:
    """图表标注/策略信号接口。

    当前先使用 JSON 文件保存用户手动买卖点、备注和预留策略信号。
    后续接入回测、自动交易和策略推荐时，不需要改前端图表，只需要向同一接口写入数据。
    """

    def __init__(self, path: str | Path | None = None) -> None:
        root = Path(__file__).resolve().parent.parent.parent
        self.path = Path(path) if path else root / "data" / "chart_annotations.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, list[dict[str, Any]]]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save(self, data: dict[str, list[dict[str, Any]]]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def list(self, symbol: str) -> list[dict[str, Any]]:
        return self._load().get(normalize_symbol(symbol), [])

    def add(self, symbol: str, item: dict[str, Any]) -> list[dict[str, Any]]:
        s = normalize_symbol(symbol)
        data = self._load()
        arr = data.setdefault(s, [])
        item = dict(item or {})
        item.setdefault("id", f"ann_{datetime.now().strftime('%Y%m%d%H%M%S%f')}")
        item.setdefault("created_at", datetime.now().isoformat(timespec="seconds"))
        item.setdefault("source", "manual")
        item.setdefault("kind", "note")  # buy/sell/note/signal
        arr.append(item)
        self._save(data)
        return arr

    def clear(self, symbol: str) -> list[dict[str, Any]]:
        s = normalize_symbol(symbol)
        data = self._load()
        data[s] = []
        self._save(data)
        return []
