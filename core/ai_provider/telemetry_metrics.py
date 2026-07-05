from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Dict, List


@dataclass
class ProviderTelemetryMetrics:
    """Aggregated per-provider metrics for Stage-14.5."""

    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    retry_count: int = 0
    fallback_count: int = 0
    streaming_count: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    latencies_ms: List[float] = field(default_factory=list)

    def record_success(self, latency_ms: float = 0.0, tokens: int = 0, cost: float = 0.0, retries: int = 0, streaming: bool = False, fallback: bool = False) -> None:
        self.request_count += 1
        self.success_count += 1
        self.retry_count += retries
        self.total_tokens += tokens
        self.total_cost += cost
        if streaming:
            self.streaming_count += 1
        if fallback:
            self.fallback_count += 1
        self.latencies_ms.append(latency_ms)

    def record_failure(self, latency_ms: float = 0.0, retries: int = 0) -> None:
        self.request_count += 1
        self.failure_count += 1
        self.retry_count += retries
        self.latencies_ms.append(latency_ms)

    def p95_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        ordered = sorted(self.latencies_ms)
        index = min(len(ordered) - 1, int(round((len(ordered) - 1) * 0.95)))
        return ordered[index]

    def snapshot(self) -> Dict[str, float | int]:
        return {
            "request_count": self.request_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": (self.success_count / self.request_count) if self.request_count else 0.0,
            "retry_count": self.retry_count,
            "fallback_count": self.fallback_count,
            "streaming_count": self.streaming_count,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "average_latency_ms": mean(self.latencies_ms) if self.latencies_ms else 0.0,
            "p95_latency_ms": self.p95_latency_ms(),
        }
