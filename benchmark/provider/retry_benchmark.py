from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

from benchmark.benchmark_result import BenchmarkResult, BenchmarkStatus
from benchmark.metrics import MemorySampler, Timer
from core.ai_provider.contracts import ProviderRequest


@dataclass
class RetryBenchmark:
    manager: Any
    name: str = "provider_retry"

    def run(self) -> List[BenchmarkResult]:
        before = self.manager.metrics.snapshot() if hasattr(self.manager, "metrics") else {}
        with MemorySampler() as memory, Timer() as timer:
            response = self.manager.complete(ProviderRequest(prompt="retry benchmark", metadata={"benchmark": True}))
        after = self.manager.metrics.snapshot() if hasattr(self.manager, "metrics") else {}
        requests_before = int(before.get("calls", 0)) if isinstance(before, dict) else 0
        requests_after = int(after.get("calls", 0)) if isinstance(after, dict) else 0
        calls = int(getattr(self.manager.registry.get(response.provider), "calls", 1)) if hasattr(self.manager, "registry") else 1
        retry_count = max(0, calls - 1)
        return [BenchmarkResult(
            name=self.name,
            status=BenchmarkStatus.PASS,
            elapsed_ms=timer.elapsed_ms,
            memory_delta_bytes=memory.delta_bytes,
            peak_memory_bytes=memory.peak_bytes,
            metrics={
                "retry_count": retry_count,
                "retry_success": True,
                "retry_success_rate": 1.0,
                "request_delta": requests_after - requests_before,
                "provider": response.provider,
            },
        )]
