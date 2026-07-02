"""NTPE 1.0 Beta Stage-09.7 Workflow Benchmark framework."""
from __future__ import annotations

from typing import Any, Callable, Dict

from .workflow_metrics import WORKFLOW_BENCHMARK_STAGE, WORKFLOW_BENCHMARK_VERSION, WorkflowBenchmarkMetric
from .workflow_runner import WorkflowBenchmarkRunner
from .workflow_report import WorkflowBenchmarkReport
from .workflow_profiler import WorkflowProfiler


class WorkflowBenchmark:
    stage = WORKFLOW_BENCHMARK_STAGE
    version = WORKFLOW_BENCHMARK_VERSION

    def __init__(self, *, profiler: WorkflowProfiler | None = None, metadata: Dict[str, Any] | None = None) -> None:
        self.runner = WorkflowBenchmarkRunner(profiler=profiler, metadata=dict(metadata or {}))
        self.metadata = dict(metadata or {})

    def add_case(self, name: str, fn: Callable[[], Any], *, iterations: int = 1, category: str = "workflow", metadata: Dict[str, Any] | None = None) -> "WorkflowBenchmark":
        self.runner.add_case(name, fn, iterations=iterations, category=category, metadata=metadata)
        return self

    def run(self) -> WorkflowBenchmarkReport:
        return self.runner.run()

    def run_callable(self, name: str, fn: Callable[[], Any], *, iterations: int = 1, category: str = "workflow", metadata: Dict[str, Any] | None = None) -> WorkflowBenchmarkMetric:
        return self.runner.run_callable(name, fn, iterations=iterations, category=category, metadata=metadata)

    def manifest(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "version": self.version,
            "foundation_status": "frozen",
            "integration_status": "frozen",
            "workflow_status": "benchmark-ready",
            "additive_only": True,
            "case_count": len(self.runner.cases),
            "metadata": dict(self.metadata),
        }
