from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import tempfile
import zipfile
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any


DATABASE_TABLES = {
    "cache_state.sqlite": ["cache_state"],
    "company_profile.sqlite": ["company_profiles"],
    "feature_store.sqlite": ["features"],
    "market_cache.sqlite": [
        "assets",
        "bars",
        "intraday_points",
        "quotes",
        "screener_scores",
    ],
    "news_store.sqlite": ["news_items", "news_analysis"],
    "v323_trading_store.sqlite": [
        "paper_sessions",
        "live_sessions",
        "signals",
        "score_provenance",
        "risk_checks",
        "orders",
        "fills",
        "positions",
        "account_snapshots",
        "account_equity_curve",
        "broker_accounts",
        "broker_positions",
        "broker_orders",
        "broker_trades",
        "broker_raw_responses",
        "ledger_entries",
        "position_lots",
        "manual_confirmations",
        "chart_markers",
        "audit_events",
        "data_source_status",
        "pit_records",
        "position_review_runs",
        "position_reviews",
    ],
}


def quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def integrity_check(path: Path) -> str:
    with closing(sqlite3.connect(path)) as connection:
        return str(connection.execute("PRAGMA integrity_check").fetchone()[0])


def checkpoint(path: Path) -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()


def table_names(connection: sqlite3.Connection, schema: str) -> set[str]:
    query = (
        f"SELECT name FROM {quote_identifier(schema)}.sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return {str(row[0]) for row in connection.execute(query)}


def table_columns(connection: sqlite3.Connection, schema: str, table: str) -> list[str]:
    query = f"PRAGMA {quote_identifier(schema)}.table_info({quote_identifier(table)})"
    return [str(row[1]) for row in connection.execute(query)]


def table_count(connection: sqlite3.Connection, schema: str, table: str) -> int:
    query = f"SELECT COUNT(*) FROM {quote_identifier(schema)}.{quote_identifier(table)}"
    return int(connection.execute(query).fetchone()[0])


def create_backup(target_data: Path, stamp: str) -> Path:
    backup_dir = target_data / "migration_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    archive_path = backup_dir / f"pre_v316_merge_{stamp}.zip"
    with tempfile.TemporaryDirectory(prefix="quant-v316-backup-") as temp_name:
        temp_root = Path(temp_name)
        for database_name in DATABASE_TABLES:
            source = target_data / database_name
            if not source.exists():
                continue
            checkpoint(source)
            snapshot = temp_root / database_name
            with closing(sqlite3.connect(source)) as source_connection, closing(
                sqlite3.connect(snapshot)
            ) as backup_connection:
                source_connection.backup(backup_connection)
        for file_name in ("watchlist.json", "news_cache.json"):
            source = target_data / file_name
            if source.exists():
                shutil.copy2(source, temp_root / file_name)
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for source in sorted(temp_root.iterdir()):
                archive.write(source, arcname=source.name)
    return archive_path


def merge_database(legacy_path: Path, target_path: Path, tables: list[str]) -> dict[str, Any]:
    if not legacy_path.exists() or not target_path.exists():
        return {"status": "missing", "tables": {}}
    legacy_integrity = integrity_check(legacy_path)
    target_integrity = integrity_check(target_path)
    if legacy_integrity != "ok" or target_integrity != "ok":
        raise RuntimeError(
            f"Integrity check failed before merge: legacy={legacy_integrity}, target={target_integrity}"
        )

    result: dict[str, Any] = {"status": "ok", "tables": {}}
    connection = sqlite3.connect(target_path)
    try:
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("ATTACH DATABASE ? AS legacy", (str(legacy_path),))
        target_tables = table_names(connection, "main")
        legacy_tables = table_names(connection, "legacy")
        connection.execute("BEGIN IMMEDIATE")
        for table in tables:
            if table not in target_tables or table not in legacy_tables:
                result["tables"][table] = {"status": "missing"}
                continue
            target_columns = table_columns(connection, "main", table)
            legacy_columns = set(table_columns(connection, "legacy", table))
            common_columns = [column for column in target_columns if column in legacy_columns]
            if table == "news_items":
                common_columns = [column for column in common_columns if column != "id"]
            if not common_columns:
                result["tables"][table] = {"status": "no_common_columns"}
                continue
            before = table_count(connection, "main", table)
            legacy_count = table_count(connection, "legacy", table)
            column_sql = ", ".join(quote_identifier(column) for column in common_columns)
            sql = (
                f"INSERT OR IGNORE INTO main.{quote_identifier(table)} ({column_sql}) "
                f"SELECT {column_sql} FROM legacy.{quote_identifier(table)}"
            )
            connection.execute(sql)
            after = table_count(connection, "main", table)
            result["tables"][table] = {
                "status": "merged",
                "legacy": legacy_count,
                "before": before,
                "inserted": after - before,
                "after": after,
            }
        connection.commit()
        connection.execute("DETACH DATABASE legacy")
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    final_integrity = integrity_check(target_path)
    if final_integrity != "ok":
        raise RuntimeError(f"Integrity check failed after merge for {target_path}: {final_integrity}")
    result["integrity"] = final_integrity
    return result


def merge_json_dictionary(legacy_path: Path, target_path: Path) -> dict[str, int]:
    legacy = json.loads(legacy_path.read_text(encoding="utf-8")) if legacy_path.exists() else {}
    target = json.loads(target_path.read_text(encoding="utf-8")) if target_path.exists() else {}
    if not isinstance(legacy, dict) or not isinstance(target, dict):
        raise ValueError("news_cache.json must contain a JSON object")
    merged = {**legacy, **target}
    temp_path = target_path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(target_path)
    return {"legacy": len(legacy), "before": len(target), "after": len(merged)}


def merge_watchlist(legacy_path: Path, target_path: Path) -> dict[str, Any]:
    legacy = json.loads(legacy_path.read_text(encoding="utf-8")) if legacy_path.exists() else {}
    target = json.loads(target_path.read_text(encoding="utf-8")) if target_path.exists() else {}
    legacy_symbols = [str(item).strip() for item in legacy.get("symbols", []) if str(item).strip()]
    target_symbols = [str(item).strip() for item in target.get("symbols", []) if str(item).strip()]
    symbols = list(dict.fromkeys([*target_symbols, *legacy_symbols]))
    payload = {"symbols": symbols, "updated_at": datetime.now().isoformat(timespec="seconds")}
    temp_path = target_path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(target_path)
    return {
        "legacy": len(legacy_symbols),
        "before": len(target_symbols),
        "added": [symbol for symbol in symbols if symbol not in target_symbols],
        "after": len(symbols),
    }


def merge_backtests(legacy_dir: Path, target_dir: Path) -> dict[str, int]:
    target_dir.mkdir(parents=True, exist_ok=True)
    before = len(list(target_dir.glob("*.json")))
    copied = 0
    invalid = 0
    for source in sorted(legacy_dir.glob("*.json")):
        destination = target_dir / source.name
        if destination.exists():
            continue
        try:
            json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            invalid += 1
            continue
        shutil.copy2(source, destination)
        copied += 1
    return {"before": before, "copied": copied, "invalid": invalid, "after": before + copied}


def migrate(legacy_root: Path, target_root: Path) -> dict[str, Any]:
    legacy_root = legacy_root.resolve()
    target_root = target_root.resolve()
    if legacy_root == target_root:
        raise ValueError("Legacy and target roots must be different")
    legacy_data = legacy_root / "data"
    target_data = target_root / "data"
    if not legacy_data.is_dir() or not target_data.is_dir():
        raise FileNotFoundError("Both projects must contain a data directory")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report: dict[str, Any] = {
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "legacy_root": str(legacy_root),
        "target_root": str(target_root),
        "policy": "target_wins; legacy_only_records_are_added",
    }
    report["backup"] = str(create_backup(target_data, stamp))
    report["databases"] = {}
    for database_name, tables in DATABASE_TABLES.items():
        report["databases"][database_name] = merge_database(
            legacy_data / database_name,
            target_data / database_name,
            tables,
        )
    report["watchlist"] = merge_watchlist(
        legacy_data / "watchlist.json", target_data / "watchlist.json"
    )
    report["news_cache"] = merge_json_dictionary(
        legacy_data / "news_cache.json", target_data / "news_cache.json"
    )
    report["backtest_runs"] = merge_backtests(
        legacy_data / "backtest_runs", target_data / "backtest_runs"
    )
    report["completed_at"] = datetime.now().isoformat(timespec="seconds")

    report_path = target_data / "migration_backups" / f"v316_merge_report_{stamp}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["report_path"] = str(report_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge V3.16 runtime history into the current package without overwriting current rows."
    )
    parser.add_argument("--legacy-root", required=True, type=Path)
    parser.add_argument("--target-root", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(migrate(args.legacy_root, args.target_root), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
