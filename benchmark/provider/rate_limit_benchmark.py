from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

from benchmark.benchmark_result import BenchmarkResult, BenchmarkStatus
from benchmark.metrics import MemorySampler, Timer
from core.ai_provider.contracts import ProviderRequest, ProviderError


@dataclass
class RateLimitBenchmark:
    manager: Any
    attempts: int = 3
    name: str = "provider_rate_limit"

    def run(self) -> List[BenchmarkResult]:
        successes = 0
        rate_limited = 0
        with MemorySampler() as memory, Timer() as timer:
            for i in range(self.attempts):
                try:
                    self.manager.complete(ProviderRequest(prompt=f"rate limit {i}", metadata={"benchmark": True}))
                    successes += 1
                except ProviderError as exc:
                    if "rate limit" in str(exc).lower():
                        rate_limited += 1
                    else:
                        raise
        return [BenchmarkResult(
            name=self.name,
            status=BenchmarkStatus.PASS,
            elapsed_ms=timer.elapsed_ms,
            memory_delta_bytes=memory.delta_bytes,
            peak_memory_bytes=memory.peak_bytes,
            metrics={
                "attempts": self.attempts,
                "successes": successes,
                "rpm_hits": rate_limited,
                "rate_limited": rate_limited,
                "queue_time_ms": 0.0,
                "wait_time_ms": 0.0,
                "effective_throughput": successes / max(timer.elapsed_ms / 1000.0, 0.000001),
            },
        )]
