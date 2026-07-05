from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping


@dataclass
class ProviderRuntimeDiagnostics:
    """Converts telemetry metrics into operational diagnostics."""

    min_success_rate: float = 0.80
    max_p95_latency_ms: float = 30000.0

    def evaluate_provider(self, provider: str, metrics: Mapping[str, object]) -> Dict[str, object]:
        request_count = int(metrics.get("request_count", 0) or 0)
        success_rate = float(metrics.get("success_rate", 0.0) or 0.0)
        p95_latency = float(metrics.get("p95_latency_ms", 0.0) or 0.0)
        issues = []
        if request_count and success_rate < self.min_success_rate:
            issues.append("low_success_rate")
        if p95_latency > self.max_p95_latency_ms:
            issues.append("high_latency")
        return {
            "provider": provider,
            "healthy": not issues,
            "issues": issues,
            "success_rate": success_rate,
            "p95_latency_ms": p95_latency,
            "request_count": request_count,
        }

    def evaluate(self, provider_metrics: Mapping[str, Mapping[str, object]]) -> Dict[str, object]:
        providers = {provider: self.evaluate_provider(provider, metrics) for provider, metrics in provider_metrics.items()}
        return {
            "healthy": all(item["healthy"] for item in providers.values()),
            "providers": providers,
        }
