from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from benchmark.benchmark_context import BenchmarkContext
from benchmark.benchmark_result import BenchmarkResult, BenchmarkStatus
from benchmark.metrics import MemorySampler, Timer


@dataclass
class RuntimeBenchmark:
    """Measure lightweight Production Runtime level operations.

    This class intentionally uses duck typing so it can benchmark the current
    Stage-01 runtime host without introducing a new dependency on its concrete
    implementation. If no runtime is provided, it runs a deterministic in-memory
    baseline workload for CI-safe benchmarks.
    """

    runtime: Any | None = None
    name: str = "runtime_benchmark"
    segments: List[Any] = field(default_factory=list)

    def benchmark_startup(self, context: BenchmarkContext | None = None) -> BenchmarkResult:
        with MemorySampler() as memory, Timer() as timer:
            runtime = self.runtime
            if runtime is not None:
                if hasattr(runtime, "start"):
                    runtime.start()
                elif hasattr(runtime, "bootstrap"):
                    runtime.bootstrap()
            else:
                # Deterministic tiny workload to make startup measurable.
                _ = {"runtime": "baseline", "metadata": dict((context or BenchmarkContext()).metadata)}
        return BenchmarkResult(
            name="runtime_startup",
            status=BenchmarkStatus.PASS,
            elapsed_ms=timer.elapsed_ms,
            memory_delta_bytes=memory.delta_bytes,
            peak_memory_bytes=memory.peak_bytes,
            metrics={"runtime_attached": self.runtime is not None},
        )

    def benchmark_job_creation(self, job_payload: Dict[str, Any] | None = None) -> BenchmarkResult:
        payload = job_payload or {"job_id": "bench-job", "segments": list(self.segments)}
        with MemorySampler() as memory, Timer() as timer:
            runtime = self.runtime
            if runtime is not None and hasattr(runtime, "create_job"):
                job = runtime.create_job(payload)
            else:
                job = {"id": payload.get("job_id", "bench-job"), "segments": payload.get("segments", [])}
        return BenchmarkResult(
            name="runtime_job_creation",
            status=BenchmarkStatus.PASS,
            elapsed_ms=timer.elapsed_ms,
            memory_delta_bytes=memory.delta_bytes,
            peak_memory_bytes=memory.peak_bytes,
            metrics={"segment_count": len(job.get("segments", [])) if isinstance(job, dict) else len(self.segments)},
        )

    def benchmark_segment_throughput(self, segments: Iterable[Any] | None = None) -> BenchmarkResult:
        segment_list = list(segments if segments is not None else (self.segments or range(10)))
        with MemorySampler() as memory, Timer() as timer:
            processed = 0
            runtime = self.runtime
            for segment in segment_list:
                if runtime is not None and hasattr(runtime, "process_segment"):
                    runtime.process_segment(segment)
                else:
                    str(segment).upper()
                processed += 1
        elapsed_seconds = max(timer.elapsed_ms / 1000.0, 0.000001)
        return BenchmarkResult(
            name="runtime_segment_throughput",
            status=BenchmarkStatus.PASS,
            elapsed_ms=timer.elapsed_ms,
            memory_delta_bytes=memory.delta_bytes,
            peak_memory_bytes=memory.peak_bytes,
            metrics={
                "segments": processed,
                "segments_per_second": processed / elapsed_seconds,
            },
        )

    def run(self, context: BenchmarkContext | None = None) -> List[BenchmarkResult]:
        ctx = context or BenchmarkContext()
        return [
            self.benchmark_startup(ctx),
            self.benchmark_job_creation(),
            self.benchmark_segment_throughput(),
        ]


def run_runtime_benchmark(runtime: Any | None = None, segments: Iterable[Any] | None = None) -> List[BenchmarkResult]:
    return RuntimeBenchmark(runtime=runtime, segments=list(segments or range(10))).run()
