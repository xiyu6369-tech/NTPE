"""Priority task queue for NTPE Stage-09.3."""
from __future__ import annotations
import heapq
from typing import List
from .task_models import Task, TaskStatus

class TaskQueue:
    def __init__(self) -> None:
        self._heap: List[Task] = []

    def push(self, task: Task) -> Task:
        task.mark(TaskStatus.QUEUED)
        heapq.heappush(self._heap, task)
        return task

    def pop(self) -> Task | None:
        while self._heap:
            task = heapq.heappop(self._heap)
            if not task.cancelled:
                return task
            return task
        return None

    def empty(self) -> bool:
        return not self._heap

    def __len__(self) -> int:
        return len(self._heap)

    def snapshot(self) -> list[dict]:
        return [task.to_dict() for task in sorted(self._heap)]
