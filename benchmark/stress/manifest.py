from __future__ import annotations

from typing import Any, Dict

STRESS_BENCHMARK_VERSION = "1.0.0-beta-stage-05.3"


def get_stress_benchmark_manifest() -> Dict[str, Any]:
    return {
        "name": "ntpe-stress-soak-benchmark",
        "version": STRESS_BENCHMARK_VERSION,
        "stage": "beta-stage-05.3",
        "capabilities": [
            "stress_runner",
            "soak_runner",
            "workload_generator",
            "failure_injection",
            "memory_monitor",
            "checkpoint_validation",
            "stress_report",
        ],
        "foundation_compatible": True,
        "backward_compatible": True,
    }
