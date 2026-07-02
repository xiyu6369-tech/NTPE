"""Task registry for NTPE Stage-09.3."""
from __future__ import annotations
from typing import Dict, Iterable
from .task_models import Task

class TaskRegistry:
    def __init__(self) -> None:
        self._items: Dict[str, Task] = {}

    def register(self, task: Task) -> Task:
        self._items[task.task_id] = task
        return task

    def get(self, task_id: str) -> Task:
        if task_id not in self._items:
            raise KeyError(f"task not registered: {task_id}")
        return self._items[task_id]

    def all(self) -> Iterable[Task]:
        return tuple(self._items.values())

    def ids(self) -> list[str]:
        return sorted(self._items.keys())

    def by_status(self, status: str) -> list[Task]:
        return [task for task in self._items.values() if task.status.value == status]

    def manifest(self) -> dict:
        return {"count": len(self._items), "tasks": self.ids()}
