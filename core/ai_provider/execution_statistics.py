from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Dict, List

from .contracts import CostStatistics, TokenUsage


@dataclass
class ExecutionStatistics:
    total_requests: int = 0
    success_count: int = 0
    failure_count: int = 0
    timeout_count: int = 0
    cancelled_count: int = 0
    retry_count: int = 0
    streaming_count: int = 0
    latencies_ms: List[float] = field(default_factory=list)
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    cost: CostStatistics = field(default_factory=CostStatistics)

    def record_success(self, latency_ms: float, usage: TokenUsage | None = None, cost: CostStatistics | None = None, retries: int = 0, streaming: bool = False) -> None:
        self.total_requests += 1
        self.success_count += 1
        self.retry_count += retries
        if streaming:
            self.streaming_count += 1
        self.latencies_ms.append(latency_ms)
        if usage:
            self.token_usage.prompt_tokens += usage.prompt_tokens
            self.token_usage.completion_tokens += usage.completion_tokens
            self.token_usage.total_tokens += usage.total_tokens
        if cost:
            self.cost.input_cost += cost.input_cost
            self.cost.output_cost += cost.output_cost
            self.cost.total_cost += cost.total_cost

    def record_failure(self, latency_ms: float = 0.0, retries: int = 0, timed_out: bool = False, cancelled: bool = False) -> None:
        self.total_requests += 1
        self.failure_count += 1
        self.retry_count += retries
        if timed_out:
            self.timeout_count += 1
        if cancelled:
            self.cancelled_count += 1
        self.latencies_ms.append(latency_ms)

    def p95_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        ordered = sorted(self.latencies_ms)
        index = min(len(ordered) - 1, int(round((len(ordered) - 1) * 0.95)))
        return ordered[index]

    def snapshot(self) -> Dict[str, object]:
        return {
            "total_requests": self.total_requests,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": (self.success_count / self.total_requests) if self.total_requests else 0.0,
            "average_latency_ms": mean(self.latencies_ms) if self.latencies_ms else 0.0,
            "p95_latency_ms": self.p95_latency_ms(),
            "retry_count": self.retry_count,
            "timeout_count": self.timeout_count,
            "cancelled_count": self.cancelled_count,
            "streaming_count": self.streaming_count,
            "token_usage": self.token_usage.to_dict(),
            "cost": self.cost.to_dict(),
        }
