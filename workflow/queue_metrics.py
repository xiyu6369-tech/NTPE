"""Queue metrics for NTPE Stage-09.3."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from .task_models import Task, TaskStatus

@dataclass
class QueueMetrics:
    queued: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0
    running: int = 0
    total: int = 0

    @classmethod
    def from_tasks(cls, tasks: list[Task]) -> "QueueMetrics":
        metrics = cls(total=len(tasks))
        for task in tasks:
            if task.status == TaskStatus.QUEUED:
                metrics.queued += 1
            elif task.status == TaskStatus.COMPLETED:
                metrics.completed += 1
            elif task.status == TaskStatus.FAILED:
                metrics.failed += 1
            elif task.status == TaskStatus.CANCELLED:
                metrics.cancelled += 1
            elif task.status == TaskStatus.RUNNING:
                metrics.running += 1
        return metrics

    def to_dict(self) -> Dict[str, int]:
        return {
            "queued": self.queued,
            "completed": self.completed,
            "failed": self.failed,
            "cancelled": self.cancelled,
            "running": self.running,
            "total": self.total,
        }
