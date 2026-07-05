from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from .contracts import CostStatistics, TokenUsage


@dataclass
class ProviderMetrics:
    calls: int = 0
    successes: int = 0
    failures: int = 0
    total_latency_ms: float = 0.0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    by_provider: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def record(
        self,
        provider: str,
        success: bool,
        latency_ms: float = 0.0,
        usage: TokenUsage | None = None,
        cost: CostStatistics | None = None,
    ):
        usage = usage or TokenUsage()
        cost = cost or CostStatistics()
        self.calls += 1
        self.successes += 1 if success else 0
        self.failures += 0 if success else 1
        self.total_latency_ms += latency_ms
        self.total_prompt_tokens += usage.prompt_tokens
        self.total_completion_tokens += usage.completion_tokens
        self.total_tokens += usage.total_tokens
        self.total_cost += cost.total_cost
        row = self.by_provider.setdefault(
            provider,
            {
                "calls": 0,
                "successes": 0,
                "failures": 0,
                "latency_ms": 0.0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
            },
        )
        row["calls"] += 1
        row["successes"] += 1 if success else 0
        row["failures"] += 0 if success else 1
        row["latency_ms"] += latency_ms
        row["prompt_tokens"] += usage.prompt_tokens
        row["completion_tokens"] += usage.completion_tokens
        row["total_tokens"] += usage.total_tokens
        row["total_cost"] += cost.total_cost

    def snapshot(self):
        avg = self.total_latency_ms / self.calls if self.calls else 0.0
        return {
            "calls": self.calls,
            "successes": self.successes,
            "failures": self.failures,
            "avg_latency_ms": avg,
            "token_usage": {
                "prompt_tokens": self.total_prompt_tokens,
                "completion_tokens": self.total_completion_tokens,
                "total_tokens": self.total_tokens,
            },
            "cost_statistics": {"total_cost": self.total_cost, "currency": "USD"},
            "by_provider": self.by_provider,
        }
