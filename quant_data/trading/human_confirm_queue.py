from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class HumanConfirmTask:
    task_id: str
    symbol: str
    action: str
    reason: str
    risk_flags: list[str] = field(default_factory=list)
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    decided_at: str | None = None
    operator: str = "paper_user"
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HumanConfirmQueue:
    """In-memory paper-only human confirmation queue."""

    def __init__(self) -> None:
        self.tasks: dict[str, HumanConfirmTask] = {}

    def enqueue(
        self,
        *,
        symbol: str,
        action: str,
        reason: str,
        risk_flags: list[str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> HumanConfirmTask:
        for existing in self.tasks.values():
            if (
                existing.status == "pending"
                and existing.symbol == str(symbol)
                and existing.action == str(action)
            ):
                return existing
        task = HumanConfirmTask(
            task_id=f"hc-{uuid4().hex[:12]}",
            symbol=str(symbol),
            action=str(action),
            reason=str(reason),
            risk_flags=list(risk_flags or []),
            payload=dict(payload or {}),
        )
        self.tasks[task.task_id] = task
        return task

    def approve(self, task_id: str, *, operator: str = "paper_user") -> HumanConfirmTask:
        return self._decide(task_id, "approved", operator)

    def reject(self, task_id: str, *, operator: str = "paper_user") -> HumanConfirmTask:
        return self._decide(task_id, "rejected", operator)

    def list(self, *, status: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        rows = list(self.tasks.values())
        if status:
            rows = [x for x in rows if x.status == status]
        rows.sort(key=lambda x: x.created_at, reverse=True)
        return [x.to_dict() for x in rows[: max(1, int(limit or 200))]]

    def _decide(self, task_id: str, status: str, operator: str) -> HumanConfirmTask:
        if task_id not in self.tasks:
            raise KeyError(f"confirm task not found: {task_id}")
        task = self.tasks[task_id]
        task.status = status
        task.operator = operator
        task.decided_at = datetime.now().isoformat(timespec="seconds")
        return task
