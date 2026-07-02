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

# Stage-08.7 Integration Benchmark exports
from .benchmark_metrics import INTEGRATION_BENCHMARK_STAGE, INTEGRATION_BENCHMARK_VERSION, IntegrationBenchmarkMetrics
from .benchmark_report import IntegrationBenchmarkReport
from .integration_benchmark import IntegrationBenchmark
from .load_test import IntegrationLoadTest
from .performance_profiler import PerformanceProfiler
from .stress_test import IntegrationStressTest

__all__ += [
    "INTEGRATION_BENCHMARK_STAGE",
    "INTEGRATION_BENCHMARK_VERSION",
    "IntegrationBenchmarkMetrics",
    "IntegrationBenchmarkReport",
    "IntegrationBenchmark",
    "IntegrationLoadTest",
    "PerformanceProfiler",
    "IntegrationStressTest",
]

# Stage-09.7 Workflow Benchmark exports
from .workflow_metrics import WORKFLOW_BENCHMARK_STAGE, WORKFLOW_BENCHMARK_VERSION, WorkflowBenchmarkMetric
from .workflow_report import WorkflowBenchmarkReport
from .workflow_profiler import WorkflowProfiler
from .workflow_runner import WorkflowBenchmarkRunner
from .workflow_suite import WorkflowBenchmarkSuite
from .workflow_load_test import WorkflowLoadTest
from .workflow_stress_test import WorkflowStressTest
from .workflow_benchmark import WorkflowBenchmark

__all__ += [
    "WORKFLOW_BENCHMARK_STAGE",
    "WORKFLOW_BENCHMARK_VERSION",
    "WorkflowBenchmarkMetric",
    "WorkflowBenchmarkReport",
    "WorkflowProfiler",
    "WorkflowBenchmarkRunner",
    "WorkflowBenchmarkSuite",
    "WorkflowLoadTest",
    "WorkflowStressTest",
    "WorkflowBenchmark",
]
