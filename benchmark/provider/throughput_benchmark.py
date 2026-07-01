from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List

from benchmark.benchmark_result import BenchmarkResult, BenchmarkStatus
from benchmark.metrics import MemorySampler, Timer
from core.ai_provider.contracts import ProviderRequest


@dataclass
class ThroughputBenchmark:
    provider: Any
    prompts: Iterable[str] | None = None
    name: str = "provider_throughput"

    def run(self) -> List[BenchmarkResult]:
        prompts = list(self.prompts or ["segment one", "segment two", "segment three", "segment four"])
        characters = 0
        tokens = 0
        with MemorySampler() as memory, Timer() as timer:
            for prompt in prompts:
                response = self.provider.complete(ProviderRequest(prompt=prompt, metadata={"benchmark": True}))
                text = response.text or ""
                characters += len(text)
                tokens += max(1, len(text.split())) if text else 0
        elapsed_seconds = max(timer.elapsed_ms / 1000.0, 0.000001)
        return [BenchmarkResult(
            name=self.name,
            status=BenchmarkStatus.PASS,
            elapsed_ms=timer.elapsed_ms,
            memory_delta_bytes=memory.delta_bytes,
            peak_memory_bytes=memory.peak_bytes,
            metrics={
                "requests": len(prompts),
                "segments_per_minute": len(prompts) / elapsed_seconds * 60.0,
                "requests_per_minute": len(prompts) / elapsed_seconds * 60.0,
                "tokens_per_second": tokens / elapsed_seconds,
                "characters_per_second": characters / elapsed_seconds,
                "tokens": tokens,
                "characters": characters,
            },
        )]


def run_throughput_benchmark(provider: Any, prompts: Iterable[str] | None = None) -> List[BenchmarkResult]:
    return ThroughputBenchmark(provider=provider, prompts=prompts).run()
