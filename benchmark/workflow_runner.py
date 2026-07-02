"""Workflow benchmark runner for Stage-09.7."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

from .workflow_profiler import WorkflowProfiler
from .workflow_report import WorkflowBenchmarkReport
from .workflow_metrics import WorkflowBenchmarkMetric

WorkflowCase = Tuple[str, Callable[[], Any], int, str, Dict[str, Any]]


class WorkflowBenchmarkRunner:
    def __init__(self, *, profiler: WorkflowProfiler | None = None, metadata: Dict[str, Any] | None = None) -> None:
        self.profiler = profiler or WorkflowProfiler()
        self.metadata = dict(metadata or {})
        self.cases: List[WorkflowCase] = []

    def add_case(self, name: str, fn: Callable[[], Any], *, iterations: int = 1, category: str = "workflow", metadata: Dict[str, Any] | None = None) -> "WorkflowBenchmarkRunner":
        self.cases.append((name, fn, max(1, int(iterations)), category, dict(metadata or {})))
        return self

    def run(self) -> WorkflowBenchmarkReport:
        report = WorkflowBenchmarkReport(metadata=dict(self.metadata))
        for name, fn, iterations, category, metadata in self.cases:
            report.add(self.profiler.profile(name, fn, iterations=iterations, category=category, metadata=metadata))
        return report

    def run_callable(self, name: str, fn: Callable[[], Any], *, iterations: int = 1, category: str = "workflow", metadata: Dict[str, Any] | None = None) -> WorkflowBenchmarkMetric:
        return self.profiler.profile(name, fn, iterations=iterations, category=category, metadata=metadata)
