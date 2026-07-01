from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

from benchmark.benchmark_result import BenchmarkResult, BenchmarkStatus
from benchmark.metrics import MemorySampler, Timer


@dataclass
class HealthBenchmark:
    manager: Any
    name: str = "provider_health"

    def run(self) -> List[BenchmarkResult]:
        with MemorySampler() as memory, Timer() as timer:
            health = self.manager.health() if hasattr(self.manager, "health") else {}
        total = len(health)
        healthy = sum(1 for item in health.values() if item.get("healthy")) if isinstance(health, dict) else 0
        return [BenchmarkResult(
            name=self.name,
            status=BenchmarkStatus.PASS,
            elapsed_ms=timer.elapsed_ms,
            memory_delta_bytes=memory.delta_bytes,
            peak_memory_bytes=memory.peak_bytes,
            metrics={
                "providers": total,
                "healthy": healthy,
                "availability": healthy / max(total, 1),
                "health": health,
            },
        )]
