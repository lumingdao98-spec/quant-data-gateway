from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .models import BacktestResult


class BacktestStorage:
    def __init__(self, root: str | Path = "data/backtest_runs") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, result: BacktestResult | dict[str, Any]) -> str:
        data = result.to_dict() if hasattr(result, "to_dict") else dict(result)
        run_id = str(data["run_id"])
        path = self.root / f"{run_id}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return run_id

    def load(self, run_id: str) -> dict[str, Any]:
        path = self.root / f"{run_id}.json"
        if not path.exists():
            raise FileNotFoundError(run_id)
        return json.loads(path.read_text(encoding="utf-8"))

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = []
        for path in sorted(self.root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            rows.append(
                {
                    "run_id": data.get("run_id"),
                    "status": data.get("status"),
                    "symbols": data.get("symbols", []),
                    "strategy": (data.get("config") or {}).get("strategy"),
                    "metrics": data.get("metrics", {}),
                    "ended_at": data.get("ended_at"),
                }
            )
        return rows

    def delete(self, run_id: str) -> bool:
        path = self.root / f"{run_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def export_json(self, run_id: str) -> str:
        return json.dumps(self.load(run_id), ensure_ascii=False, indent=2)

    def export_trades_csv(self, run_id: str, path: str | Path | None = None) -> Path:
        data = self.load(run_id)
        output = Path(path) if path else self.root / f"{run_id}-trades.csv"
        trades = data.get("trades", [])
        fieldnames = sorted({k for trade in trades for k in trade.keys()}) or ["run_id"]
        with output.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for trade in trades:
                writer.writerow(trade)
        return output
