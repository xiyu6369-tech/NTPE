"""Workflow load test helpers for Stage-09.7."""
from __future__ import annotations

from typing import Any, Callable, Dict

from .workflow_profiler import WorkflowProfiler


class WorkflowLoadTest:
    def __init__(self, *, profiler: WorkflowProfiler | None = None) -> None:
        self.profiler = profiler or WorkflowProfiler()

    def run(self, name: str, fn: Callable[[int], Any], *, operations: int = 10, category: str = "load") -> Dict[str, Any]:
        operations = max(1, int(operations))
        counter = {"value": 0}

        def execute() -> Any:
            index = counter["value"]
            counter["value"] += 1
            return fn(index)

        metric = self.profiler.profile(name, execute, iterations=operations, category=category, metadata={"mode": "load", "operations": operations})
        data = metric.to_dict()
        data["stable"] = metric.passed
        return data
