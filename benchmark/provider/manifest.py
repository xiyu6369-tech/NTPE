from __future__ import annotations

from typing import Any, Dict


def build_provider_benchmark_manifest() -> Dict[str, Any]:
    return {
        "name": "ntpe.provider.benchmark",
        "version": "1.0-beta-stage-05.2",
        "stage": "beta-stage-05.2",
        "foundation_compatibility": "foundation-v1.0-frozen",
        "requires": ["beta-stage-03-ai-provider", "beta-stage-05.0-benchmark-framework"],
        "capabilities": [
            "provider_latency",
            "first_token_latency",
            "completion_latency",
            "provider_throughput",
            "tokens_per_second",
            "requests_per_minute",
            "retry_benchmark",
            "fallback_benchmark",
            "rate_limit_benchmark",
            "provider_health",
            "provider_metrics",
            "json_report",
            "regression_ready",
        ],
    }


def attach_provider_benchmark_manifest(payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    result = dict(payload or {})
    result["provider_benchmark"] = build_provider_benchmark_manifest()
    return result
