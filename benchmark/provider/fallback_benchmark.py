from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

from benchmark.benchmark_result import BenchmarkResult, BenchmarkStatus
from benchmark.metrics import MemorySampler, Timer
from core.ai_provider.contracts import ProviderRequest


@dataclass
class FallbackBenchmark:
    manager: Any
    name: str = "provider_fallback"

    def run(self) -> List[BenchmarkResult]:
        with MemorySampler() as memory, Timer() as timer:
            response = self.manager.complete(ProviderRequest(prompt="fallback benchmark", metadata={"benchmark": True}))
        preferred = self.manager.router.default_provider if hasattr(self.manager, "router") else None
        fallback_triggered = bool(preferred and response.provider != preferred)
        return [BenchmarkResult(
            name=self.name,
            status=BenchmarkStatus.PASS,
            elapsed_ms=timer.elapsed_ms,
            memory_delta_bytes=memory.delta_bytes,
            peak_memory_bytes=memory.peak_bytes,
            metrics={
                "fallback_triggered": fallback_triggered,
                "fallback_count": 1 if fallback_triggered else 0,
                "switch_time_ms": timer.elapsed_ms,
                "recovery_time_ms": timer.elapsed_ms,
                "provider": response.provider,
            },
        )]
