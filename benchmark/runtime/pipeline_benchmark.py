from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, List

from benchmark.benchmark_result import BenchmarkResult, BenchmarkStatus
from benchmark.metrics import MemorySampler, Timer

PipelineStep = Callable[[Any], Any]


def _identity(value: Any) -> Any:
    return value


@dataclass
class PipelineBenchmark:
    """Benchmark pipeline latency and throughput with callable stages."""

    steps: List[PipelineStep] = field(default_factory=lambda: [_identity])
    name: str = "pipeline_benchmark"

    def execute_once(self, payload: Any) -> Any:
        current = payload
        for step in self.steps:
            current = step(current)
        return current

    def benchmark_latency(self, payload: Any = "segment") -> BenchmarkResult:
        with MemorySampler() as memory, Timer() as timer:
            output = self.execute_once(payload)
        return BenchmarkResult(
            name="pipeline_latency",
            status=BenchmarkStatus.PASS,
            elapsed_ms=timer.elapsed_ms,
            memory_delta_bytes=memory.delta_bytes,
            peak_memory_bytes=memory.peak_bytes,
            metrics={"step_count": len(self.steps), "output_present": output is not None},
        )

    def benchmark_throughput(self, payloads: Iterable[Any] | None = None) -> BenchmarkResult:
        values = list(payloads if payloads is not None else range(25))
        with MemorySampler() as memory, Timer() as timer:
            count = 0
            for value in values:
                self.execute_once(value)
                count += 1
        elapsed_seconds = max(timer.elapsed_ms / 1000.0, 0.000001)
        return BenchmarkResult(
            name="pipeline_throughput",
            status=BenchmarkStatus.PASS,
            elapsed_ms=timer.elapsed_ms,
            memory_delta_bytes=memory.delta_bytes,
            peak_memory_bytes=memory.peak_bytes,
            metrics={"items": count, "items_per_second": count / elapsed_seconds},
        )

    def run(self) -> List[BenchmarkResult]:
        return [self.benchmark_latency(), self.benchmark_throughput()]


def run_pipeline_benchmark(steps: List[PipelineStep] | None = None) -> List[BenchmarkResult]:
    return PipelineBenchmark(steps=steps or [_identity]).run()
