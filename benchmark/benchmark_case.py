from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Protocol

from .benchmark_context import BenchmarkContext
from .benchmark_result import BenchmarkResult, BenchmarkStatus


class BenchmarkCallable(Protocol):
    def __call__(self, context: BenchmarkContext) -> Any: ...


class BenchmarkCase:
    name: str

    def run(self, context: BenchmarkContext) -> BenchmarkResult:
        raise NotImplementedError


@dataclass
class FunctionBenchmarkCase(BenchmarkCase):
    name: str
    fn: BenchmarkCallable
    metadata: Dict[str, Any] = field(default_factory=dict)

    def run(self, context: BenchmarkContext) -> BenchmarkResult:
        value = self.fn(context.child(**self.metadata))
        metrics: Dict[str, Any] = {}
        if isinstance(value, BenchmarkResult):
            return value
        if isinstance(value, dict):
            metrics.update(value)
        elif value is not None:
            metrics["value"] = value
        return BenchmarkResult(name=self.name, status=BenchmarkStatus.PASS, metrics=metrics)
