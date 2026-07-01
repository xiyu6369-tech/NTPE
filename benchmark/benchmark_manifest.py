from __future__ import annotations

from typing import Any, Dict


def build_benchmark_manifest() -> Dict[str, Any]:
    return {
        "name": "NTPE Benchmark Framework",
        "stage": "NTPE 1.0 Beta Stage-05.0",
        "version": "0.5.0",
        "status": "beta",
        "capabilities": [
            "benchmark_case",
            "benchmark_registry",
            "benchmark_runner",
            "benchmark_suite",
            "timer_metrics",
            "memory_sampler",
            "json_report",
        ],
        "foundation_compatibility": "foundation-v1.0 frozen compatible",
        "backward_compatible": True,
    }
