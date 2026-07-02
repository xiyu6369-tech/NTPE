from __future__ import annotations

from typing import Any, Dict

PERFORMANCE_REPORT_VERSION = "1.0-beta-stage-05.4"


def get_performance_report_manifest() -> Dict[str, Any]:
    return {
        "name": "ntpe.performance.report",
        "version": PERFORMANCE_REPORT_VERSION,
        "stage": "beta-stage-05.4",
        "foundation_compatibility": "foundation-v1.0-frozen",
        "foundation_compatible": True,
        "backward_compatible": True,
        "requires": [
            "beta-stage-05.0-benchmark-framework",
            "beta-stage-05.1-runtime-benchmark",
            "beta-stage-05.2-provider-benchmark",
            "beta-stage-05.3-stress-soak-test",
        ],
        "capabilities": [
            "performance_report",
            "benchmark_summary",
            "json_report",
            "html_report",
            "dashboard",
            "regression_analysis",
            "trend_analysis",
            "runtime_report",
            "provider_report",
            "stress_report",
            "soak_report",
        ],
    }


def attach_performance_report_manifest(payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    result = dict(payload or {})
    result["performance_report"] = get_performance_report_manifest()
    return result
