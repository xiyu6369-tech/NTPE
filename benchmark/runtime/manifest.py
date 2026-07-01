from __future__ import annotations

from typing import Any, Dict


def build_runtime_benchmark_manifest() -> Dict[str, Any]:
    return {
        "name": "ntpe.runtime.benchmark",
        "version": "1.0-beta-stage-05.1",
        "stage": "beta-stage-05.1",
        "foundation_compatibility": "foundation-v1.0-frozen",
        "capabilities": [
            "runtime_startup",
            "job_creation",
            "segment_throughput",
            "pipeline_latency",
            "pipeline_throughput",
            "session_checkpoint",
            "session_resume",
            "recovery_latency",
            "memory_usage",
            "json_report",
        ],
    }


def attach_runtime_benchmark_manifest(payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    result = dict(payload or {})
    result["runtime_benchmark"] = build_runtime_benchmark_manifest()
    return result
