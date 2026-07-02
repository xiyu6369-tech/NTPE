"""Workflow benchmark suite composition for Stage-09.7."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable

from .workflow_runner import WorkflowBenchmarkRunner
from .workflow_report import WorkflowBenchmarkReport


class WorkflowBenchmarkSuite:
    def __init__(self, name: str = "workflow", *, metadata: Dict[str, Any] | None = None) -> None:
        self.name = name
        self.metadata = dict(metadata or {})
        self.runner = WorkflowBenchmarkRunner(metadata={"suite": name, **self.metadata})

    def add(self, name: str, fn: Callable[[], Any], *, iterations: int = 1, category: str = "workflow", metadata: Dict[str, Any] | None = None) -> "WorkflowBenchmarkSuite":
        self.runner.add_case(name, fn, iterations=iterations, category=category, metadata=metadata)
        return self

    def extend(self, cases: Iterable[tuple[str, Callable[[], Any]]], *, iterations: int = 1, category: str = "workflow") -> "WorkflowBenchmarkSuite":
        for name, fn in cases:
            self.add(name, fn, iterations=iterations, category=category)
        return self

    def run(self) -> WorkflowBenchmarkReport:
        return self.runner.run()
