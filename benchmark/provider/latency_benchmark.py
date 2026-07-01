from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Iterable, List

from benchmark.benchmark_context import BenchmarkContext
from benchmark.benchmark_result import BenchmarkResult, BenchmarkStatus
from benchmark.metrics import MemorySampler, Timer
from core.ai_provider.contracts import ProviderRequest, ProviderResponse


@dataclass
class LatencyBenchmark:
    provider: Any
    prompts: Iterable[str] | None = None
    name: str = "provider_latency"

    def run(self, context: BenchmarkContext | None = None) -> List[BenchmarkResult]:
        prompts = list(self.prompts or ["hello", "world", "benchmark"])
        latencies = []
        first_token_latencies = []
        responses = []
        with MemorySampler() as memory, Timer() as timer:
            for prompt in prompts:
                start = time.time()
                response = self.provider.complete(ProviderRequest(prompt=prompt, metadata={"benchmark": True}))
                elapsed_ms = response.latency_ms or (time.time() - start) * 1000
                latencies.append(elapsed_ms)
                first_token_latencies.append(float(response.metadata.get("first_token_latency_ms", elapsed_ms)))
                responses.append(response)
        avg = sum(latencies) / len(latencies) if latencies else 0.0
        first_avg = sum(first_token_latencies) / len(first_token_latencies) if first_token_latencies else 0.0
        return [
            BenchmarkResult(
                name=self.name,
                status=BenchmarkStatus.PASS,
                elapsed_ms=timer.elapsed_ms,
                memory_delta_bytes=memory.delta_bytes,
                peak_memory_bytes=memory.peak_bytes,
                metrics={
                    "requests": len(prompts),
                    "avg_latency_ms": avg,
                    "first_token_latency_ms": first_avg,
                    "completion_latency_ms": avg,
                    "providers": list({getattr(r, "provider", "unknown") for r in responses}),
                },
            )
        ]


def run_latency_benchmark(provider: Any, prompts: Iterable[str] | None = None) -> List[BenchmarkResult]:
    return LatencyBenchmark(provider=provider, prompts=prompts).run()
