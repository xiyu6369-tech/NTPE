import pytest

from core.ai_provider import (
    ExecutionContext,
    ExecutionLimits,
    ExecutionScheduler,
    MockProvider,
    ProviderError,
    ProviderRequest,
    ProviderRuntimeExecutionPolicy,
    RateLimiter,
    RetryPolicy,
)


def test_execution_policy_retries_and_records_statistics():
    provider = MockProvider(name="retry-provider", response_text="ok {prompt}", fail_times=1)
    policy = ProviderRuntimeExecutionPolicy(retry_policy=RetryPolicy(max_attempts=2), rate_limiter=RateLimiter(max_calls=1000))

    result = policy.execute(provider, ProviderRequest(prompt="text"))

    assert result.text == "ok text"
    assert result.retry_count == 1
    assert policy.statistics.snapshot()["success_count"] == 1
    assert any(event.name == "execution.retry" for event in policy.event_bus.history)


def test_execution_policy_budget_rejects_non_retryable():
    provider = MockProvider(name="budget-provider", response_text="too many tokens")
    policy = ProviderRuntimeExecutionPolicy(
        retry_policy=RetryPolicy(max_attempts=3),
        rate_limiter=RateLimiter(max_calls=1000),
        limits=ExecutionLimits(max_total_tokens=1),
    )

    with pytest.raises(ProviderError):
        policy.execute(provider, ProviderRequest(prompt="prompt"))

    assert policy.statistics.snapshot()["failure_count"] == 1


def test_execution_policy_streaming_and_cancellation():
    provider = MockProvider(name="stream-provider", response_text="stream text")
    policy = ProviderRuntimeExecutionPolicy(rate_limiter=RateLimiter(max_calls=1000))

    chunks = list(policy.stream(provider, ProviderRequest(prompt="x", stream=True)))

    assert chunks[-1].done is True
    assert policy.statistics.snapshot()["streaming_count"] == 1

    ctx = ExecutionContext(request=ProviderRequest(prompt="x"), provider_name="stream-provider")
    ctx.cancel()
    with pytest.raises(ProviderError):
        policy.execute(provider, ProviderRequest(prompt="x"), context=ctx)


def test_execution_scheduler_priority_order():
    scheduler = ExecutionScheduler[str](mode="priority")
    scheduler.submit("low", priority=1)
    scheduler.submit("high", priority=10)

    assert scheduler.drain() == ["high", "low"]
