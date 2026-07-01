from __future__ import annotations

from collections import OrderedDict
from typing import Iterable, List

from .benchmark_case import BenchmarkCase


class BenchmarkRegistry:
    def __init__(self) -> None:
        self._cases: "OrderedDict[str, BenchmarkCase]" = OrderedDict()

    def register(self, case: BenchmarkCase, *, replace: bool = False) -> BenchmarkCase:
        if not replace and case.name in self._cases:
            raise ValueError(f"Benchmark already registered: {case.name}")
        self._cases[case.name] = case
        return case

    def get(self, name: str) -> BenchmarkCase:
        return self._cases[name]

    def list(self) -> List[str]:
        return list(self._cases.keys())

    def values(self) -> Iterable[BenchmarkCase]:
        return self._cases.values()

    def clear(self) -> None:
        self._cases.clear()
