"""Deterministic stress test helpers for Stage-08.7."""
from __future__ import annotations

from typing import Any, Callable, Dict

from .performance_profiler import PerformanceProfiler


class IntegrationStressTest:
    def __init__(self, *, profiler: PerformanceProfiler | None = None) -> None:
        self.profiler = profiler or PerformanceProfiler()

    def run(self, name: str, fn: Callable[[], Any], *, cycles: int = 25) -> Dict[str, Any]:
        cycles = max(1, int(cycles))
        metric = self.profiler.profile(name, fn, iterations=cycles, metadata={"mode": "stress", "cycles": cycles})
        data = metric.to_dict()
        data["stable"] = metric.passed and metric.elapsed_ms >= 0
        return data
