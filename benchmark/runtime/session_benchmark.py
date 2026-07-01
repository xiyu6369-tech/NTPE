from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from benchmark.benchmark_result import BenchmarkResult, BenchmarkStatus
from benchmark.metrics import MemorySampler, Timer


@dataclass
class SessionBenchmark:
    """Benchmark session checkpoint and resume operations."""

    session: Any | None = None
    state: Dict[str, Any] = field(default_factory=lambda: {"session_id": "bench-session", "offset": 0})

    def benchmark_checkpoint(self) -> BenchmarkResult:
        with MemorySampler() as memory, Timer() as timer:
            if self.session is not None and hasattr(self.session, "checkpoint"):
                checkpoint = self.session.checkpoint()
            else:
                checkpoint = dict(self.state)
                checkpoint["checkpointed"] = True
        return BenchmarkResult(
            name="session_checkpoint",
            status=BenchmarkStatus.PASS,
            elapsed_ms=timer.elapsed_ms,
            memory_delta_bytes=memory.delta_bytes,
            peak_memory_bytes=memory.peak_bytes,
            metrics={"checkpoint_created": bool(checkpoint)},
        )

    def benchmark_resume(self) -> BenchmarkResult:
        with MemorySampler() as memory, Timer() as timer:
            if self.session is not None and hasattr(self.session, "resume"):
                resumed = self.session.resume()
            else:
                resumed = dict(self.state)
                resumed["resumed"] = True
        return BenchmarkResult(
            name="session_resume_latency",
            status=BenchmarkStatus.PASS,
            elapsed_ms=timer.elapsed_ms,
            memory_delta_bytes=memory.delta_bytes,
            peak_memory_bytes=memory.peak_bytes,
            metrics={"resumed": bool(resumed)},
        )

    def run(self) -> List[BenchmarkResult]:
        return [self.benchmark_checkpoint(), self.benchmark_resume()]


def run_session_benchmark(session: Any | None = None) -> List[BenchmarkResult]:
    return SessionBenchmark(session=session).run()
