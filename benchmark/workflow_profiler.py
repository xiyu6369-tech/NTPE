"""Deterministic workflow profiler for Stage-09.7."""
from __future__ import annotations

from typing import Any, Callable, Dict

from .metrics import MemorySampler, Timer
from .workflow_metrics import WorkflowBenchmarkMetric


class WorkflowProfiler:
    def profile(self, name: str, fn: Callable[[], Any], *, iterations: int = 1, category: str = "workflow", metadata: Dict[str, Any] | None = None) -> WorkflowBenchmarkMetric:
        iterations = max(1, int(iterations))
        last_value: Any = None
        with MemorySampler() as memory, Timer() as timer:
            for _ in range(iterations):
                last_value = fn()
        elapsed_ms = timer.elapsed_ms
        seconds = max(elapsed_ms / 1000.0, 0.000001)
        data = dict(metadata or {})
        if last_value is not None:
            data["last_value_type"] = type(last_value).__name__
        return WorkflowBenchmarkMetric(
            name=name,
            iterations=iterations,
            elapsed_ms=elapsed_ms,
            throughput_ops_per_sec=iterations / seconds,
            memory_delta_bytes=memory.delta_bytes,
            peak_memory_bytes=memory.peak_bytes,
            passed=True,
            category=category,
            metadata=data,
        )
