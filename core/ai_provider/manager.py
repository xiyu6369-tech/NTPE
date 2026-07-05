from __future__ import annotations

import time
from typing import Iterator, Optional

from .contracts import ProviderError, ProviderRequest, ProviderResponse, ProviderStreamChunk
from .events import ProviderEvent, ProviderEventBus
from .fallback import FallbackStrategy
from .health import HealthMonitor
from .metrics import ProviderMetrics
from .rate_limiter import RateLimiter
from .registry import ProviderRegistry
from .retry import RetryPolicy
from .router import ProviderRouter


class ProviderManager:
    def __init__(
        self,
        registry: Optional[ProviderRegistry] = None,
        router: Optional[ProviderRouter] = None,
        retry_policy: Optional[RetryPolicy] = None,
        rate_limiter: Optional[RateLimiter] = None,
        fallback: Optional[FallbackStrategy] = None,
        metrics: Optional[ProviderMetrics] = None,
        event_bus: Optional[ProviderEventBus] = None,
    ):
        self.registry = registry or ProviderRegistry()
        self.router = router or ProviderRouter()
        self.retry_policy = retry_policy or RetryPolicy()
        self.rate_limiter = rate_limiter or RateLimiter(max_calls=10**9)
        self.fallback = fallback or FallbackStrategy()
        self.metrics = metrics or ProviderMetrics()
        self.health_monitor = HealthMonitor()
        self.event_bus = event_bus or ProviderEventBus()

    def _provider_chain(self, request: ProviderRequest):
        preferred = self.router.route(request) or self.registry.default_name()
        chain = self.fallback.chain(preferred)
        return chain or ([preferred] if preferred else [])

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        last = None
        for provider_name in self._provider_chain(request):
            if not provider_name:
                continue
            provider = self.registry.get(provider_name)
            if not self.rate_limiter.allow(provider_name):
                last = ProviderError("rate limit exceeded", provider_name, True, status_code=429)
                self.metrics.record(provider_name, False, 0)
                continue
            start = time.time()
            self.event_bus.publish(ProviderEvent("provider.request", provider_name, {"model": request.model}))
            try:
                response = self.retry_policy.run(lambda: provider.complete(request))
                response.latency_ms = response.latency_ms or (time.time() - start) * 1000
                self.metrics.record(provider_name, True, response.latency_ms, response.usage, response.cost)
                self.event_bus.publish(
                    ProviderEvent(
                        "provider.response",
                        provider_name,
                        {
                            "success": True,
                            "model": response.model,
                            "usage": response.usage.to_dict(),
                            "cost": response.cost.to_dict(),
                        },
                    )
                )
                return response
            except ProviderError as exc:
                last = exc
                self.metrics.record(provider_name, False, (time.time() - start) * 1000)
                self.event_bus.publish(ProviderEvent("provider.error", provider_name, {"error": str(exc)}))
                if not exc.retryable:
                    break
        raise last or ProviderError("no provider available", self.registry.default_name(), True)

    def stream(self, request: ProviderRequest) -> Iterator[ProviderStreamChunk]:
        request.stream = True
        response_text = []
        last_chunk = None
        provider_name = self.router.route(request) or self.registry.default_name()
        if not provider_name:
            raise ProviderError("no provider available", None, True)
        provider = self.registry.get(provider_name)
        if not self.rate_limiter.allow(provider_name):
            raise ProviderError("rate limit exceeded", provider_name, True, status_code=429)
        self.event_bus.publish(ProviderEvent("provider.stream.start", provider_name, {"model": request.model}))
        try:
            for chunk in provider.stream(request):
                response_text.append(chunk.text)
                last_chunk = chunk
                yield chunk
            self.metrics.record(provider_name, True, 0)
            self.event_bus.publish(
                ProviderEvent("provider.stream.end", provider_name, {"chunks": (last_chunk.index + 1) if last_chunk else 0})
            )
        except ProviderError as exc:
            self.metrics.record(provider_name, False, 0)
            self.event_bus.publish(ProviderEvent("provider.stream.error", provider_name, {"error": str(exc)}))
            raise

    def health(self):
        return {name: self.health_monitor.check(self.registry.get(name)) for name in self.registry.list()}

    def manifest(self):
        return {
            "component": "ai_provider",
            "stage": "NTPE 1.2 Professional Stage-14",
            "version": "1.2-professional-stage-14",
            "providers": self.registry.list(),
            "registry": self.registry.manifest(),
            "retry_policy": self.retry_policy.to_dict(),
            "rate_limit": self.rate_limiter.snapshot(),
            "metrics": self.metrics.snapshot(),
        }
