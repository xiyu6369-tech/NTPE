from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from benchmark.benchmark_context import BenchmarkContext
from benchmark.benchmark_result import BenchmarkResult, BenchmarkStatus
from benchmark.metrics import Timer

from .memory_monitor import MemoryMonitor
from .stress_runner import StressRunner
from .workload_generator import generate_workload


@dataclass
class SoakRunner:
    iterations: int = 3
    segment_count: int = 10
    name: str = "soak_runner"

    def run(self, context: BenchmarkContext | None = None) -> BenchmarkResult:
        if self.iterations < 1:
            raise ValueError("iterations must be >= 1")
        monitor = MemoryMonitor()
        iteration_metrics: List[Dict[str, Any]] = []
        with Timer() as timer:
            monitor.sample("start")
            for index in range(self.iterations):
                workload = generate_workload(segment_count=self.segment_count, name=f"soak-{index + 1}")
                result = StressRunner(workload=workload, name=f"soak_iteration_{index + 1}").run(context)
                if not result.is_passed():
                    return BenchmarkResult(name=self.name, status=BenchmarkStatus.FAIL, error=result.error or "soak iteration failed")
                iteration_metrics.append(result.metrics)
                monitor.sample(f"iteration-{index + 1}")
        monitor.stop()
        total_segments = self.iterations * self.segment_count
        elapsed_seconds = max(timer.elapsed_ms / 1000.0, 0.000001)
        return BenchmarkResult(
            name=self.name,
            status=BenchmarkStatus.PASS,
            elapsed_ms=timer.elapsed_ms,
            metrics={
                "iterations": self.iterations,
                "segments": total_segments,
                "segments_per_second": total_segments / elapsed_seconds,
                "memory_trend": monitor.trend(),
                "iteration_metrics": iteration_metrics,
            },
        )


def run_soak_benchmark(iterations: int = 3, segment_count: int = 10) -> BenchmarkResult:
    return SoakRunner(iterations=iterations, segment_count=segment_count).run()
