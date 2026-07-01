from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List


@dataclass
class ProviderBenchmarkMetrics:
    requests: int = 0
    successes: int = 0
    failures: int = 0
    retries: int = 0
    fallbacks: int = 0
    rate_limited: int = 0
    timeouts: int = 0
    latencies_ms: List[float] = field(default_factory=list)
    tokens: int = 0
    characters: int = 0

    def record_latency(self, latency_ms: float) -> None:
        self.latencies_ms.append(float(latency_ms))

    def record_success(self, latency_ms: float = 0.0, text: str = "") -> None:
        self.requests += 1
        self.successes += 1
        self.record_latency(latency_ms)
        self.characters += len(text or "")
        self.tokens += max(1, len((text or "").split())) if text else 0

    def record_failure(self, latency_ms: float = 0.0, timeout: bool = False) -> None:
        self.requests += 1
        self.failures += 1
        self.record_latency(latency_ms)
        if timeout:
            self.timeouts += 1

    def snapshot(self) -> Dict[str, Any]:
        return summarize_provider_metrics(self)


def percentile(values: Iterable[float], p: float) -> float:
    items = sorted(float(v) for v in values)
    if not items:
        return 0.0
    if len(items) == 1:
        return items[0]
    rank = (len(items) - 1) * p
    lower = int(rank)
    upper = min(lower + 1, len(items) - 1)
    weight = rank - lower
    return items[lower] * (1 - weight) + items[upper] * weight


def summarize_provider_metrics(metrics: ProviderBenchmarkMetrics) -> Dict[str, Any]:
    total = max(metrics.requests, 1)
    latencies = list(metrics.latencies_ms)
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    elapsed_seconds = max(sum(latencies) / 1000.0, 0.000001)
    return {
        "requests": metrics.requests,
        "successes": metrics.successes,
        "failures": metrics.failures,
        "success_rate": metrics.successes / total,
        "error_rate": metrics.failures / total,
        "retry_count": metrics.retries,
        "fallback_count": metrics.fallbacks,
        "rate_limited": metrics.rate_limited,
        "timeout_count": metrics.timeouts,
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": percentile(latencies, 0.95),
        "p99_latency_ms": percentile(latencies, 0.99),
        "tokens": metrics.tokens,
        "characters": metrics.characters,
        "tokens_per_second": metrics.tokens / elapsed_seconds,
        "characters_per_second": metrics.characters / elapsed_seconds,
    }
