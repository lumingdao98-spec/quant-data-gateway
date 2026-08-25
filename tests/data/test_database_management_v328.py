from __future__ import annotations

import sqlite3

import pytest

from quant_data.services.database_management_service import DatabaseManagementService


def test_database_inventory_is_allowlisted_and_reports_rows(tmp_path):
    db_path = tmp_path / "managed.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE samples (id INTEGER PRIMARY KEY, value TEXT)")
        conn.executemany("INSERT INTO samples(value) VALUES (?)", [("a",), ("b",)])
        conn.commit()
    service = DatabaseManagementService(
        {"managed": {"path": db_path, "label": "测试库", "purpose": "测试数据"}}
    )

    inventory = service.inventory()

    assert inventory["ok"] is True
    assert inventory["database_count"] == 1
    assert inventory["data"][0]["quick_check"] == "ok"
    assert inventory["data"][0]["tables"] == [{"name": "samples", "rows": 2}]
    assert "任意 SQL" in inventory["policy"]
    with pytest.raises(KeyError):
        service.inspect("../managed")


def test_database_checkpoint_does_not_delete_business_rows(tmp_path):
    db_path = tmp_path / "wal.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE records (id INTEGER PRIMARY KEY, value TEXT)")
        conn.executemany("INSERT INTO records(value) VALUES (?)", [(str(i),) for i in range(20)])
        conn.commit()
    service = DatabaseManagementService({"managed": {"path": db_path}})

    result = service.checkpoint("managed", truncate=True)

    assert result["ok"] is True
    assert result["mode"] == "truncate"
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 20
