"""NTPE 1.0 Beta Stage-05.0 Benchmark Framework.

This package is intentionally independent from frozen Foundation contracts.
It provides a lightweight benchmark framework used by later Stage-05 modules.
"""

from .benchmark_case import BenchmarkCase, FunctionBenchmarkCase
from .benchmark_context import BenchmarkContext
from .benchmark_manifest import build_benchmark_manifest
from .benchmark_registry import BenchmarkRegistry
from .benchmark_result import BenchmarkResult, BenchmarkStatus
from .benchmark_runner import BenchmarkRunner
from .benchmark_suite import BenchmarkSuite

__all__ = [
    "BenchmarkCase",
    "FunctionBenchmarkCase",
    "BenchmarkContext",
    "BenchmarkRegistry",
    "BenchmarkResult",
    "BenchmarkRunner",
    "BenchmarkStatus",
    "BenchmarkSuite",
    "build_benchmark_manifest",
]
