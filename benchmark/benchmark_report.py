"""Benchmark report model for Stage-08.7."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from .benchmark_metrics import IntegrationBenchmarkMetrics, INTEGRATION_BENCHMARK_STAGE, INTEGRATION_BENCHMARK_VERSION


@dataclass
class IntegrationBenchmarkReport:
    metrics: List[IntegrationBenchmarkMetrics] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return all(item.passed for item in self.metrics)

    def add(self, metric: IntegrationBenchmarkMetrics) -> "IntegrationBenchmarkReport":
        self.metrics.append(metric)
        return self

    def extend(self, metrics: Iterable[IntegrationBenchmarkMetrics]) -> "IntegrationBenchmarkReport":
        self.metrics.extend(metrics)
        return self

    def summary(self) -> Dict[str, Any]:
        total_elapsed = sum(item.elapsed_ms for item in self.metrics)
        return {
            "stage": INTEGRATION_BENCHMARK_STAGE,
            "version": INTEGRATION_BENCHMARK_VERSION,
            "foundation_status": "frozen",
            "ok": self.ok,
            "count": len(self.metrics),
            "total_elapsed_ms": round(total_elapsed, 6),
            "metrics": [item.to_dict() for item in self.metrics],
            "metadata": dict(self.metadata),
        }
