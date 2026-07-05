from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Iterator, Optional

from .contracts import ProviderError, ProviderRequest, ProviderResponse, ProviderStreamChunk
from .execution_context import ExecutionContext
from .execution_events import (
    EXECUTION_CANCELLED,
    EXECUTION_COMPLETED,
    EXECUTION_FAILED,
    EXECUTION_RETRY,
    EXECUTION_STARTED,
    EXECUTION_TIMEOUT,
    ExecutionEvent,
    ExecutionEventBus,
)
from .execution_hooks import (
    AFTER_EXECUTION,
    AFTER_RETRY,
    BEFORE_EXECUTION,
    BEFORE_RETRY,
    ON_COMPLETE,
    ON_FAILURE,
    ON_TIMEOUT,
    ExecutionHookRegistry,
)
from .execution_limits import ExecutionLimits
from .execution_result import ExecutionResult
from .execution_scheduler import ExecutionScheduler
from .execution_statistics import ExecutionStatistics
from .rate_limiter import RateLimiter
from .retry import RetryPolicy


@dataclass
class ProviderRuntimeExecutionPolicy:
    """Unified execution policy for NTPE AI providers.

    Providers remain responsible for transport. This policy owns retry, timeout,
    rate limit, streaming coordination, token/cost budget validation, events,
    hooks, and runtime statistics.
    """

    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    rate_limiter: RateLimiter = field(default_factory=lambda: RateLimiter(max_calls=10**9))
    limits: ExecutionLimits = field(default_factory=ExecutionLimits)
    event_bus: ExecutionEventBus = field(default_factory=ExecutionEventBus)
    hooks: ExecutionHookRegistry = field(default_factory=ExecutionHookRegistry)
    statistics: ExecutionStatistics = field(default_factory=ExecutionStatistics)
    scheduler: ExecutionScheduler[ExecutionContext] = field(default_factory=ExecutionScheduler)
    health_check_before_execution: bool = False

    def build_context(
        self,
        request: ProviderRequest,
        provider_name: Optional[str] = None,
        session_id: Optional[str] = None,
        runtime_id: Optional[str] = None,
        priority: int = 0,
    ) -> ExecutionContext:
        return ExecutionContext(
            request=request,
            provider_name=provider_name,
            model=request.model,
            session_id=session_id,
            runtime_id=runtime_id,
            priority=priority,
            stream=request.stream,
            metadata=dict(request.metadata),
        )

    def execute(self, provider, request: ProviderRequest, context: Optional[ExecutionContext] = None) -> ExecutionResult:
        ctx = context or self.build_context(request, getattr(provider, "name", None))
        provider_name = ctx.provider_name or getattr(provider, "name", None)
        start = time.time()
        retries = 0
        self._ensure_not_cancelled(ctx)
        if not self.rate_limiter.allow(provider_name):
            raise ProviderError("rate limit exceeded", provider_name, True, status_code=429)
        if self.health_check_before_execution:
            health = provider.health()
            if not health.get("healthy", False):
                raise ProviderError("provider health check failed", provider_name, retryable=True)
        self.event_bus.publish(ExecutionEvent(EXECUTION_STARTED, provider_name, {"model": request.model}))
        self.hooks.run(BEFORE_EXECUTION, ctx, {"provider": provider_name})
        last: ProviderError | None = None
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            try:
                self._ensure_not_cancelled(ctx)
                response = provider.complete(request)
                elapsed = (time.time() - start) * 1000
                response.latency_ms = response.latency_ms or elapsed
                self._validate_elapsed(start, provider_name)
                self.limits.validate_usage(response.usage, provider_name)
                self.limits.validate_cost(response.cost, provider_name)
                result = ExecutionResult(
                    response=response,
                    context=ctx,
                    attempts=attempt,
                    provider_name=provider_name,
                    retry_count=retries,
                    metadata={"policy": "provider_runtime_execution_policy"},
                )
                self.statistics.record_success(response.latency_ms, response.usage, response.cost, retries=retries)
                self.hooks.run(AFTER_EXECUTION, ctx, {"result": result})
                self.hooks.run(ON_COMPLETE, ctx, {"result": result})
                self.event_bus.publish(
                    ExecutionEvent(
                        EXECUTION_COMPLETED,
                        provider_name,
                        {"attempts": attempt, "retry_count": retries, "latency_ms": response.latency_ms},
                    )
                )
                return result
            except ProviderError as exc:
                last = exc
                timed_out = "timeout" in str(exc).lower()
                if timed_out:
                    self.event_bus.publish(ExecutionEvent(EXECUTION_TIMEOUT, provider_name, {"error": str(exc)}))
                    self.hooks.run(ON_TIMEOUT, ctx, {"error": exc})
                if not exc.retryable or attempt >= self.retry_policy.max_attempts:
                    elapsed = (time.time() - start) * 1000
                    self.statistics.record_failure(elapsed, retries=retries, timed_out=timed_out, cancelled=ctx.cancelled)
                    self.event_bus.publish(ExecutionEvent(EXECUTION_FAILED, provider_name, {"error": str(exc), "attempts": attempt}))
                    self.hooks.run(ON_FAILURE, ctx, {"error": exc})
                    raise
                retries += 1
                self.hooks.run(BEFORE_RETRY, ctx, {"attempt": attempt, "error": exc})
                self.event_bus.publish(ExecutionEvent(EXECUTION_RETRY, provider_name, {"attempt": attempt, "error": str(exc)}))
                delay = self.retry_policy.base_delay_seconds * (self.retry_policy.backoff_factor ** (attempt - 1))
                if delay:
                    time.sleep(delay)
                self.hooks.run(AFTER_RETRY, ctx, {"attempt": attempt})
        raise last or ProviderError("execution failed", provider_name, True)

    def stream(self, provider, request: ProviderRequest, context: Optional[ExecutionContext] = None) -> Iterator[ProviderStreamChunk]:
        request.stream = True
        ctx = context or self.build_context(request, getattr(provider, "name", None))
        provider_name = ctx.provider_name or getattr(provider, "name", None)
        start = time.time()
        chunks = 0
        self._ensure_not_cancelled(ctx)
        if not self.rate_limiter.allow(provider_name):
            raise ProviderError("rate limit exceeded", provider_name, True, status_code=429)
        self.event_bus.publish(ExecutionEvent(EXECUTION_STARTED, provider_name, {"stream": True, "model": request.model}))
        self.hooks.run(BEFORE_EXECUTION, ctx, {"provider": provider_name, "stream": True})
        try:
            for chunk in provider.stream(request):
                self._ensure_not_cancelled(ctx)
                self._validate_stream_elapsed(start, provider_name)
                chunks += 1
                yield chunk
            elapsed = (time.time() - start) * 1000
            self.statistics.record_success(elapsed, streaming=True)
            self.hooks.run(ON_COMPLETE, ctx, {"chunks": chunks})
            self.event_bus.publish(ExecutionEvent(EXECUTION_COMPLETED, provider_name, {"stream": True, "chunks": chunks}))
        except ProviderError as exc:
            elapsed = (time.time() - start) * 1000
            timed_out = "timeout" in str(exc).lower()
            self.statistics.record_failure(elapsed, timed_out=timed_out, cancelled=ctx.cancelled)
            self.event_bus.publish(ExecutionEvent(EXECUTION_FAILED, provider_name, {"stream": True, "error": str(exc)}))
            self.hooks.run(ON_FAILURE, ctx, {"error": exc})
            raise

    def cancel(self, context: ExecutionContext) -> None:
        context.cancel()
        self.event_bus.publish(ExecutionEvent(EXECUTION_CANCELLED, context.provider_name, context.to_dict()))

    def manifest(self) -> dict[str, object]:
        return {
            "component": "provider_runtime_execution_policy",
            "stage": "NTPE 1.2 Professional Stage-14.3",
            "retry_policy": self.retry_policy.to_dict(),
            "rate_limit": self.rate_limiter.snapshot(),
            "limits": self.limits.to_dict(),
            "scheduler": self.scheduler.manifest(),
            "hooks": self.hooks.manifest(),
            "statistics": self.statistics.snapshot(),
            "health_check_before_execution": self.health_check_before_execution,
        }

    def _ensure_not_cancelled(self, context: ExecutionContext) -> None:
        if context.cancelled:
            self.statistics.record_failure(cancelled=True)
            self.event_bus.publish(ExecutionEvent(EXECUTION_CANCELLED, context.provider_name, context.to_dict()))
            raise ProviderError("execution cancelled", context.provider_name, retryable=False)

    def _validate_elapsed(self, start: float, provider_name: Optional[str]) -> None:
        if self.limits.total_timeout_seconds is not None and time.time() - start > self.limits.total_timeout_seconds:
            raise ProviderError("total execution timeout exceeded", provider_name, retryable=True)
        if self.limits.request_timeout_seconds is not None and time.time() - start > self.limits.request_timeout_seconds:
            raise ProviderError("request timeout exceeded", provider_name, retryable=True)

    def _validate_stream_elapsed(self, start: float, provider_name: Optional[str]) -> None:
        if self.limits.stream_timeout_seconds is not None and time.time() - start > self.limits.stream_timeout_seconds:
            self.event_bus.publish(ExecutionEvent(EXECUTION_TIMEOUT, provider_name, {}))
            raise ProviderError("stream timeout exceeded", provider_name, retryable=True)
        self._validate_elapsed(start, provider_name)
