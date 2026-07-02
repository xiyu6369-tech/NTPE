from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List

from benchmark.benchmark_context import BenchmarkContext
from benchmark.benchmark_result import BenchmarkResult, BenchmarkStatus
from benchmark.metrics import Timer

from .checkpoint_validator import CheckpointValidator
from .failure_injector import FailureInjector
from .memory_monitor import MemoryMonitor
from .workload_generator import StressWorkload, generate_workload

Processor = Callable[[dict], Any]


@dataclass
class StressRunner:
    workload: StressWorkload | None = None
    processor: Processor | None = None
    failure_injector: FailureInjector | None = None
    name: str = "stress_runner"

    def _process_segment(self, segment: dict) -> Any:
        if self.processor is not None:
            return self.processor(segment)
        # CI-safe baseline workload.
        return {"id": segment.get("id"), "text": str(segment.get("text", "")).upper()}

    def run(self, context: BenchmarkContext | None = None) -> BenchmarkResult:
        workload = self.workload or generate_workload(segment_count=25)
        monitor = MemoryMonitor()
        processed_ids: List[str] = []
        failures = 0
        with Timer() as timer:
            monitor.sample("start")
            for index, segment in enumerate(workload.iter_segments()):
                try:
                    if self.failure_injector is not None:
                        self.failure_injector.execute(
                            index,
                            lambda segment=segment: self._process_segment(segment),
                            recovery=lambda exc: {"recovered": True, "error": str(exc)},
                        )
                    else:
                        self._process_segment(segment)
                    processed_ids.append(str(segment.get("id", index)))
                except Exception:
                    failures += 1
            monitor.sample("end")
        checkpoint = CheckpointValidator().build_checkpoint(processed_ids)
        validation = CheckpointValidator().validate(checkpoint, expected_ids=[str(s.get("id")) for s in workload.segments])
        elapsed_seconds = max(timer.elapsed_ms / 1000.0, 0.000001)
        injector_metrics = self.failure_injector.metrics() if self.failure_injector is not None else {}
        monitor.stop()
        return BenchmarkResult(
            name=self.name,
            status=BenchmarkStatus.PASS if validation.valid and failures == 0 else BenchmarkStatus.FAIL,
            elapsed_ms=timer.elapsed_ms,
            metrics={
                "segments": workload.size(),
                "total_chars": workload.total_chars(),
                "segments_per_second": workload.size() / elapsed_seconds,
                "failures": failures,
                "checkpoint": validation.to_dict(),
                "memory_trend": monitor.trend(),
                **injector_metrics,
            },
        )


def run_stress_benchmark(segment_count: int = 25) -> BenchmarkResult:
    return StressRunner(workload=generate_workload(segment_count=segment_count)).run()
