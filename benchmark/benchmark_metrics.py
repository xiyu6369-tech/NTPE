"""Integration benchmark metrics for NTPE Stage-08.7."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

INTEGRATION_BENCHMARK_STAGE = "NTPE 1.0 Beta Stage-08.7 Integration Benchmark"
INTEGRATION_BENCHMARK_VERSION = "0.8.7"


@dataclass
class IntegrationBenchmarkMetrics:
    name: str
    iterations: int = 1
    elapsed_ms: float = 0.0
    throughput_ops_per_sec: float = 0.0
    memory_delta_bytes: int = 0
    peak_memory_bytes: int = 0
    passed: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "iterations": int(self.iterations),
            "elapsed_ms": round(float(self.elapsed_ms), 6),
            "throughput_ops_per_sec": round(float(self.throughput_ops_per_sec), 6),
            "memory_delta_bytes": int(self.memory_delta_bytes),
            "peak_memory_bytes": int(self.peak_memory_bytes),
            "passed": bool(self.passed),
            "metadata": dict(self.metadata),
        }
