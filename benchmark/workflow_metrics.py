"""Workflow benchmark metrics for NTPE Stage-09.7."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

WORKFLOW_BENCHMARK_STAGE = "NTPE 1.0 Beta Stage-09.7 Workflow Benchmark"
WORKFLOW_BENCHMARK_VERSION = "0.9.7"


@dataclass
class WorkflowBenchmarkMetric:
    name: str
    iterations: int = 1
    elapsed_ms: float = 0.0
    throughput_ops_per_sec: float = 0.0
    memory_delta_bytes: int = 0
    peak_memory_bytes: int = 0
    passed: bool = True
    category: str = "workflow"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "iterations": int(self.iterations),
            "elapsed_ms": round(float(self.elapsed_ms), 6),
            "throughput_ops_per_sec": round(float(self.throughput_ops_per_sec), 6),
            "memory_delta_bytes": int(self.memory_delta_bytes),
            "peak_memory_bytes": int(self.peak_memory_bytes),
            "passed": bool(self.passed),
            "metadata": dict(self.metadata),
        }
