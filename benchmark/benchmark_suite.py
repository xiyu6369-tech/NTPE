from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from .benchmark_case import BenchmarkCase


@dataclass
class BenchmarkSuite:
    name: str
    cases: List[BenchmarkCase] = field(default_factory=list)

    def add(self, case: BenchmarkCase) -> "BenchmarkSuite":
        self.cases.append(case)
        return self

    def extend(self, cases: Iterable[BenchmarkCase]) -> "BenchmarkSuite":
        self.cases.extend(cases)
        return self
