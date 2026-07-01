from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from benchmark.benchmark_result import BenchmarkResult, BenchmarkStatus
from benchmark.metrics import MemorySampler, Timer


@dataclass
class RecoveryBenchmark:
    """Benchmark recovery/checkpoint restore latency."""

    recovery: Any | None = None
    checkpoint: Dict[str, Any] | None = None

    def benchmark_recovery_latency(self) -> BenchmarkResult:
        checkpoint = self.checkpoint or {"session_id": "bench-session", "chunk_index": 5}
        with MemorySampler() as memory, Timer() as timer:
            if self.recovery is not None and hasattr(self.recovery, "restore"):
                restored = self.recovery.restore(checkpoint)
            elif self.recovery is not None and hasattr(self.recovery, "recover"):
                restored = self.recovery.recover(checkpoint)
            else:
                restored = dict(checkpoint)
                restored["restored"] = True
        return BenchmarkResult(
            name="recovery_latency",
            status=BenchmarkStatus.PASS,
            elapsed_ms=timer.elapsed_ms,
            memory_delta_bytes=memory.delta_bytes,
            peak_memory_bytes=memory.peak_bytes,
            metrics={"restored": bool(restored), "checkpoint_keys": len(checkpoint)},
        )

    def run(self) -> List[BenchmarkResult]:
        return [self.benchmark_recovery_latency()]


def run_recovery_benchmark(recovery: Any | None = None) -> List[BenchmarkResult]:
    return RecoveryBenchmark(recovery=recovery).run()
