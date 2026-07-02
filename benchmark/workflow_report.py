"""Workflow benchmark report model for Stage-09.7."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from .workflow_metrics import WORKFLOW_BENCHMARK_STAGE, WORKFLOW_BENCHMARK_VERSION, WorkflowBenchmarkMetric


@dataclass
class WorkflowBenchmarkReport:
    metrics: List[WorkflowBenchmarkMetric] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return all(item.passed for item in self.metrics)

    def add(self, metric: WorkflowBenchmarkMetric) -> "WorkflowBenchmarkReport":
        self.metrics.append(metric)
        return self

    def extend(self, metrics: Iterable[WorkflowBenchmarkMetric]) -> "WorkflowBenchmarkReport":
        self.metrics.extend(metrics)
        return self

    def summary(self) -> Dict[str, Any]:
        total_elapsed = sum(item.elapsed_ms for item in self.metrics)
        categories = sorted({item.category for item in self.metrics})
        return {
            "stage": WORKFLOW_BENCHMARK_STAGE,
            "version": WORKFLOW_BENCHMARK_VERSION,
            "foundation_status": "frozen",
            "integration_status": "frozen",
            "workflow_status": "benchmark-ready",
            "ok": self.ok,
            "count": len(self.metrics),
            "categories": categories,
            "total_elapsed_ms": round(total_elapsed, 6),
            "metrics": [item.to_dict() for item in self.metrics],
            "metadata": dict(self.metadata),
        }
