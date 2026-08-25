from __future__ import annotations

from typing import Any

from quant_data.trading.human_confirm_queue import HumanConfirmQueue, HumanConfirmTask


class LiveConfirmQueue(HumanConfirmQueue):
    """Live-order confirmation queue that can be restored from SQLite rows."""

    def restore(self, rows: list[dict[str, Any]]) -> int:
        restored = 0
        for row in rows or []:
            task_id = str(row.get("task_id") or row.get("id") or "").strip()
            if not task_id:
                continue
            try:
                task = HumanConfirmTask(
                    task_id=task_id,
                    symbol=str(row.get("symbol") or ""),
                    action=str(row.get("action") or ""),
                    reason=str(row.get("reason") or ""),
                    risk_flags=list(row.get("risk_flags") or []),
                    status=str(row.get("status") or "pending"),
                    created_at=str(row.get("created_at") or ""),
                    decided_at=str(row.get("decided_at") or "") or None,
                    operator=str(row.get("operator") or "paper_user"),
                    payload=dict(row.get("payload") or {}),
                )
            except (TypeError, ValueError):
                continue
            self.tasks[task.task_id] = task
            restored += 1
        return restored
