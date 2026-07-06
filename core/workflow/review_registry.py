# =====================================================
# NTPE 1.2 Professional
# Stage-17.4 Review & Approval Layer
# =====================================================

from typing import Dict, Iterable, Optional

from .review_task import ReviewTask


class ReviewRegistry:
    def __init__(self) -> None:
        self._tasks: Dict[str, ReviewTask] = {}

    def register(self, task: ReviewTask) -> ReviewTask:
        self._tasks[task.task_id] = task
        return task

    def get(self, task_id: str) -> Optional[ReviewTask]:
        return self._tasks.get(task_id)

    def require(self, task_id: str) -> ReviewTask:
        task = self.get(task_id)
        if task is None:
            raise KeyError(f"Review task not found: {task_id}")
        return task

    def all(self) -> Iterable[ReviewTask]:
        return tuple(self._tasks.values())
