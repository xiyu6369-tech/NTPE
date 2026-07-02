"""Workflow stress test helpers for Stage-09.7."""
from __future__ import annotations

from typing import Any, Callable, Dict

from .workflow_profiler import WorkflowProfiler


class WorkflowStressTest:
    def __init__(self, *, profiler: WorkflowProfiler | None = None) -> None:
        self.profiler = profiler or WorkflowProfiler()

    def run(self, name: str, fn: Callable[[], Any], *, cycles: int = 25, category: str = "stress") -> Dict[str, Any]:
        cycles = max(1, int(cycles))
        metric = self.profiler.profile(name, fn, iterations=cycles, category=category, metadata={"mode": "stress", "cycles": cycles})
        data = metric.to_dict()
        data["stable"] = metric.passed and metric.elapsed_ms >= 0
        return data
