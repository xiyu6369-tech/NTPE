from __future__ import annotations

from typing import Iterable, List

from .benchmark_case import BenchmarkCase
from .benchmark_context import BenchmarkContext
from .benchmark_registry import BenchmarkRegistry
from .benchmark_result import BenchmarkResult, BenchmarkStatus
from .benchmark_suite import BenchmarkSuite
from .metrics import MemorySampler, Timer


class BenchmarkRunner:
    def __init__(self, context: BenchmarkContext | None = None) -> None:
        self.context = context or BenchmarkContext()

    def run_case(self, case: BenchmarkCase) -> BenchmarkResult:
        try:
            with MemorySampler() as memory, Timer() as timer:
                result = case.run(self.context)
            result.elapsed_ms = timer.elapsed_ms
            result.memory_delta_bytes = memory.delta_bytes
            result.peak_memory_bytes = memory.peak_bytes
            if not isinstance(result.status, BenchmarkStatus):
                result.status = BenchmarkStatus(result.status)
            return result
        except Exception as exc:
            return BenchmarkResult.fail(getattr(case, "name", "unknown"), exc)

    def run_cases(self, cases: Iterable[BenchmarkCase]) -> List[BenchmarkResult]:
        return [self.run_case(case) for case in cases]

    def run_registry(self, registry: BenchmarkRegistry) -> List[BenchmarkResult]:
        return self.run_cases(registry.values())

    def run_suite(self, suite: BenchmarkSuite) -> List[BenchmarkResult]:
        return self.run_cases(suite.cases)
