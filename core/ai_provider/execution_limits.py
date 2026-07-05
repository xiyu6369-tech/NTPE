from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .contracts import CostStatistics, ProviderError, TokenUsage


@dataclass
class ExecutionLimits:
    """Request/session budget guard for provider execution."""

    request_timeout_seconds: Optional[float] = None
    stream_timeout_seconds: Optional[float] = None
    total_timeout_seconds: Optional[float] = None
    max_prompt_tokens: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    max_total_tokens: Optional[int] = None
    max_request_cost: Optional[float] = None
    max_session_cost: Optional[float] = None
    currency: str = "USD"
    on_cost_exceeded: str = "reject"  # reject | warn | downgrade

    def validate_usage(self, usage: TokenUsage, provider: Optional[str] = None) -> None:
        if self.max_prompt_tokens is not None and usage.prompt_tokens > self.max_prompt_tokens:
            raise ProviderError("prompt token budget exceeded", provider, retryable=False)
        if self.max_completion_tokens is not None and usage.completion_tokens > self.max_completion_tokens:
            raise ProviderError("completion token budget exceeded", provider, retryable=False)
        if self.max_total_tokens is not None and usage.total_tokens > self.max_total_tokens:
            raise ProviderError("total token budget exceeded", provider, retryable=False)

    def validate_cost(self, cost: CostStatistics, provider: Optional[str] = None) -> None:
        if self.max_request_cost is not None and cost.total_cost > self.max_request_cost:
            if self.on_cost_exceeded == "reject":
                raise ProviderError("request cost budget exceeded", provider, retryable=False)

    def to_dict(self) -> Dict[str, object]:
        return {
            "request_timeout_seconds": self.request_timeout_seconds,
            "stream_timeout_seconds": self.stream_timeout_seconds,
            "total_timeout_seconds": self.total_timeout_seconds,
            "max_prompt_tokens": self.max_prompt_tokens,
            "max_completion_tokens": self.max_completion_tokens,
            "max_total_tokens": self.max_total_tokens,
            "max_request_cost": self.max_request_cost,
            "max_session_cost": self.max_session_cost,
            "currency": self.currency,
            "on_cost_exceeded": self.on_cost_exceeded,
        }
