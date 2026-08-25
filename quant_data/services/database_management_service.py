from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


class DatabaseManagementService:
    """Safe, allowlisted SQLite inventory and WAL maintenance.

    This service intentionally has no arbitrary-path, SQL execution, export,
    replace, or delete interface. It is suitable for a diagnostics page, not a
    general database console.
    """

    def __init__(self, databases: Mapping[str, Mapping[str, Any]]) -> None:
        self._databases: dict[str, dict[str, Any]] = {}
        for key, descriptor in databases.items():
            path = Path(str(descriptor.get("path") or "")).expanduser().resolve()
            self._databases[str(key)] = {
                "key": str(key),
                "label": str(descriptor.get("label") or key),
                "purpose": str(descriptor.get("purpose") or "本地 SQLite 数据"),
                "path": path,
            }

    def inventory(self, *, quick_check: bool = True) -> dict[str, Any]:
        rows = [self.inspect(key, quick_check=quick_check) for key in self._databases]
        existing = [row for row in rows if row.get("exists")]
        return {
            "ok": True,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "database_count": len(rows),
            "existing_count": len(existing),
            "total_size_bytes": sum(int(row.get("size_bytes") or 0) for row in existing),
            "total_wal_bytes": sum(int(row.get("wal_size_bytes") or 0) for row in existing),
            "data": rows,
            "policy": (
                "只允许查看系统白名单 SQLite、统计表行数和执行 WAL checkpoint；"
                "不提供任意 SQL、路径访问、清空或删除数据库。"
            ),
        }

    def inspect(self, key: str, *, quick_check: bool = True) -> dict[str, Any]:
        descriptor = self._descriptor(key)
        path: Path = descriptor["path"]
        wal_path = Path(f"{path}-wal")
        shm_path = Path(f"{path}-shm")
        base = {
            "key": descriptor["key"],
            "label": descriptor["label"],
            "purpose": descriptor["purpose"],
            "path": str(path),
            "exists": path.is_file(),
            "size_bytes": path.stat().st_size if path.is_file() else 0,
            "wal_size_bytes": wal_path.stat().st_size if wal_path.is_file() else 0,
            "shm_size_bytes": shm_path.stat().st_size if shm_path.is_file() else 0,
            "modified_at": (
                datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
                if path.is_file()
                else None
            ),
            "quick_check": "missing" if not path.is_file() else "not_run",
            "table_count": 0,
            "total_rows": 0,
            "tables": [],
            "error": "",
        }
        if not path.is_file():
            return base

        try:
            uri = f"{path.as_uri()}?mode=ro"
            with sqlite3.connect(uri, uri=True, timeout=2.0) as conn:
                conn.row_factory = sqlite3.Row
                if quick_check:
                    checked = conn.execute("PRAGMA quick_check(1)").fetchone()
                    base["quick_check"] = str(checked[0] if checked else "unknown")
                table_rows = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                ).fetchall()
                tables: list[dict[str, Any]] = []
                for table_row in table_rows:
                    name = str(table_row["name"])
                    quoted = name.replace('"', '""')
                    try:
                        count_row = conn.execute(f'SELECT COUNT(*) AS n FROM "{quoted}"').fetchone()
                        count = int(count_row["n"] if count_row else 0)
                        tables.append({"name": name, "rows": count})
                    except sqlite3.Error as exc:
                        tables.append({"name": name, "rows": None, "error": str(exc)[:160]})
                base["tables"] = tables
                base["table_count"] = len(tables)
                base["total_rows"] = sum(int(row.get("rows") or 0) for row in tables)
        except sqlite3.Error as exc:
            base["quick_check"] = "error"
            base["error"] = str(exc)[:240]
        return base

    def checkpoint(self, key: str, *, truncate: bool = False) -> dict[str, Any]:
        descriptor = self._descriptor(key)
        path: Path = descriptor["path"]
        if not path.is_file():
            return {"ok": False, "key": key, "message": "数据库文件不存在", "data": self.inspect(key)}
        before = self.inspect(key, quick_check=False)
        mode = "TRUNCATE" if truncate else "PASSIVE"
        try:
            with sqlite3.connect(path, timeout=5.0) as conn:
                result = conn.execute(f"PRAGMA wal_checkpoint({mode})").fetchone()
            after = self.inspect(key, quick_check=True)
            return {
                "ok": True,
                "key": key,
                "mode": mode.lower(),
                "checkpoint_result": list(result) if result else [],
                "before_wal_bytes": before.get("wal_size_bytes", 0),
                "after_wal_bytes": after.get("wal_size_bytes", 0),
                "data": after,
                "message": "WAL 检查点已完成；未删除业务数据。",
            }
        except sqlite3.Error as exc:
            return {
                "ok": False,
                "key": key,
                "mode": mode.lower(),
                "message": f"WAL 检查点失败：{str(exc)[:200]}",
                "data": self.inspect(key, quick_check=False),
            }

    def _descriptor(self, key: str) -> dict[str, Any]:
        normalized = str(key or "").strip()
        if normalized not in self._databases:
            raise KeyError(f"未知数据库：{normalized}")
        return self._databases[normalized]
