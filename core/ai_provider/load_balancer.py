from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from .contracts import ProviderError, ProviderRequest
from .execution_policy import ProviderRuntimeExecutionPolicy
from .fallback_chain import FallbackChain
from .orchestration_result import OrchestrationResult, ProviderAttempt
from .provider_pool import ProviderPool
from .routing_policy import RoutingPolicy


@dataclass
class ProviderLoadBalancer:
    """Provider load balancer for Stage-14.4.

    It routes a request to the best available provider and escalates through the
    fallback chain when a provider fails. It is deliberately built on top of the
    Stage-14.3 execution policy so retry, timeout, token budget, cost budget,
    hooks, and events remain centralized.
    """

    registry: object
    pool: ProviderPool = field(default_factory=ProviderPool)
    routing_policy: RoutingPolicy = field(default_factory=RoutingPolicy)
    fallback_chain: FallbackChain = field(default_factory=FallbackChain)
    execution_policy: ProviderRuntimeExecutionPolicy = field(default_factory=ProviderRuntimeExecutionPolicy)
    statistics: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.pool.entries(enabled_only=False):
            for name in self.registry.list():
                self.pool.add(name)

    def route(self, request: ProviderRequest) -> List[str]:
        candidates = self.routing_policy.order(self.registry, self.pool, request, self.statistics)
        return self.fallback_chain.resolve(candidates)

    def execute(self, request: ProviderRequest) -> OrchestrationResult:
        attempts: List[ProviderAttempt] = []
        candidates = self.route(request)
        if not candidates:
            raise ProviderError("no provider candidates available", None, retryable=True)
        last_error: Optional[ProviderError] = None
        for index, provider_name in enumerate(candidates):
            provider = self.registry.get(provider_name)
            try:
                result = self.execution_policy.execute(provider, request)
                response = result.response
                attempts.append(
                    ProviderAttempt(
                        provider=provider_name,
                        success=True,
                        latency_ms=response.latency_ms,
                        retry_count=result.retry_count,
                        metadata={"candidate_index": index},
                    )
                )
                self._record_success(provider_name, response.latency_ms)
                return OrchestrationResult(
                    response=response,
                    selected_provider=provider_name,
                    attempts=attempts,
                    execution_result=result,
                    fallback_used=index > 0,
                    metadata={"candidates": candidates, "stage": "NTPE 1.2 Professional Stage-14.4"},
                )
            except ProviderError as exc:
                last_error = exc
                attempts.append(ProviderAttempt(provider=provider_name, success=False, error=str(exc), metadata={"candidate_index": index}))
                self._record_failure(provider_name)
                if self.fallback_chain.stop_on_non_retryable and not exc.retryable:
                    break
        if last_error is not None:
            last_error.args = (str(last_error),)
            raise last_error
        raise ProviderError("provider orchestration failed", None, retryable=True)

    def execute_text(self, prompt: str, **kwargs) -> str:
        return self.execute(ProviderRequest(prompt=prompt, **kwargs)).response.text

    def _record_success(self, provider: str, latency_ms: float) -> None:
        stats = self.statistics.setdefault(provider, {"success_count": 0.0, "failure_count": 0.0, "average_latency_ms": 0.0})
        count = stats["success_count"]
        stats["success_count"] = count + 1
        stats["average_latency_ms"] = ((stats["average_latency_ms"] * count) + latency_ms) / max(1.0, count + 1)

    def _record_failure(self, provider: str) -> None:
        stats = self.statistics.setdefault(provider, {"success_count": 0.0, "failure_count": 0.0, "average_latency_ms": 0.0})
        stats["failure_count"] += 1

    def manifest(self) -> Dict[str, object]:
        return {
            "component": "provider_load_balancer",
            "stage": "NTPE 1.2 Professional Stage-14.4",
            "pool": self.pool.to_dict(),
            "routing_policy": self.routing_policy.to_dict(),
            "fallback_chain": self.fallback_chain.to_dict(),
            "statistics": {name: dict(values) for name, values in self.statistics.items()},
            "execution_policy": self.execution_policy.manifest(),
        }
