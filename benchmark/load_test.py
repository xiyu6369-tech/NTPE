"""Lightweight load test helpers for Stage-08.7."""
from __future__ import annotations

from typing import Any, Callable, Dict

from .performance_profiler import PerformanceProfiler


class IntegrationLoadTest:
    def __init__(self, *, profiler: PerformanceProfiler | None = None) -> None:
        self.profiler = profiler or PerformanceProfiler()

    def run(self, name: str, fn: Callable[[int], Any], *, operations: int = 10) -> Dict[str, Any]:
        operations = max(1, int(operations))
        counter = {"value": 0}

        def execute() -> Any:
            current = counter["value"]
            counter["value"] += 1
            return fn(current)

        metric = self.profiler.profile(name, execute, iterations=operations, metadata={"mode": "load", "operations": operations})
        return metric.to_dict()
