"""NTPE Stage-08.7 Integration Benchmark framework."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List

from .benchmark_metrics import INTEGRATION_BENCHMARK_STAGE, INTEGRATION_BENCHMARK_VERSION, IntegrationBenchmarkMetrics
from .benchmark_report import IntegrationBenchmarkReport
from .performance_profiler import PerformanceProfiler


class IntegrationBenchmark:
    stage = INTEGRATION_BENCHMARK_STAGE
    version = INTEGRATION_BENCHMARK_VERSION

    def __init__(self, *, profiler: PerformanceProfiler | None = None, metadata: Dict[str, Any] | None = None) -> None:
        self.profiler = profiler or PerformanceProfiler()
        self.metadata = dict(metadata or {})
        self.cases: List[tuple[str, Callable[[], Any], int, Dict[str, Any]]] = []

    def add_case(self, name: str, fn: Callable[[], Any], *, iterations: int = 1, metadata: Dict[str, Any] | None = None) -> "IntegrationBenchmark":
        self.cases.append((name, fn, max(1, int(iterations)), dict(metadata or {})))
        return self

    def run(self) -> IntegrationBenchmarkReport:
        report = IntegrationBenchmarkReport(metadata=dict(self.metadata))
        for name, fn, iterations, metadata in self.cases:
            report.add(self.profiler.profile(name, fn, iterations=iterations, metadata=metadata))
        return report

    def run_callable(self, name: str, fn: Callable[[], Any], *, iterations: int = 1, metadata: Dict[str, Any] | None = None) -> IntegrationBenchmarkMetrics:
        return self.profiler.profile(name, fn, iterations=iterations, metadata=metadata)

    def manifest(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "version": self.version,
            "foundation_status": "frozen",
            "case_count": len(self.cases),
            "metadata": dict(self.metadata),
        }
