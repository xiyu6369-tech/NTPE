from __future__ import annotations
import time
from typing import Optional
from .contracts import ProviderRequest, ProviderResponse, ProviderError
from .registry import ProviderRegistry
from .router import ProviderRouter
from .retry import RetryPolicy
from .rate_limiter import RateLimiter
from .fallback import FallbackStrategy
from .metrics import ProviderMetrics
from .health import HealthMonitor
from .events import ProviderEventBus, ProviderEvent

class ProviderManager:
    def __init__(self, registry: Optional[ProviderRegistry] = None, router: Optional[ProviderRouter] = None,
                 retry_policy: Optional[RetryPolicy] = None, rate_limiter: Optional[RateLimiter] = None,
                 fallback: Optional[FallbackStrategy] = None, metrics: Optional[ProviderMetrics] = None,
                 event_bus: Optional[ProviderEventBus] = None):
        self.registry = registry or ProviderRegistry()
        self.router = router or ProviderRouter()
        self.retry_policy = retry_policy or RetryPolicy()
        self.rate_limiter = rate_limiter or RateLimiter(max_calls=10**9)
        self.fallback = fallback or FallbackStrategy()
        self.metrics = metrics or ProviderMetrics()
        self.health_monitor = HealthMonitor()
        self.event_bus = event_bus or ProviderEventBus()
    def complete(self, request: ProviderRequest) -> ProviderResponse:
        preferred = self.router.route(request) or self.registry.default_name()
        chain = self.fallback.chain(preferred)
        if not chain:
            chain = [preferred]
        last = None
        for provider_name in chain:
            if not provider_name:
                continue
            provider = self.registry.get(provider_name)
            if not self.rate_limiter.allow():
                last = ProviderError("rate limit exceeded", provider_name, True)
                self.metrics.record(provider_name, False, 0)
                continue
            start = time.time()
            self.event_bus.publish(ProviderEvent("provider.request", provider_name, {"model": request.model}))
            try:
                def run_once():
                    return provider.complete(request)
                response = self.retry_policy.run(run_once)
                response.latency_ms = response.latency_ms or (time.time() - start) * 1000
                self.metrics.record(provider_name, True, response.latency_ms)
                self.event_bus.publish(ProviderEvent("provider.response", provider_name, {"success": True}))
                return response
            except ProviderError as exc:
                last = exc
                self.metrics.record(provider_name, False, (time.time() - start) * 1000)
                self.event_bus.publish(ProviderEvent("provider.error", provider_name, {"error": str(exc)}))
                if not exc.retryable:
                    break
        raise last or ProviderError("no provider available", preferred, True)
    def health(self):
        return {name: self.health_monitor.check(self.registry.get(name)) for name in self.registry.list()}
    def manifest(self):
        return {"component": "ai_provider", "version": "1.0-beta-stage-03", "providers": self.registry.list(), "metrics": self.metrics.snapshot()}
