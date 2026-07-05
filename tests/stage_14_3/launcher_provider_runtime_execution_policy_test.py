import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.ai_provider import (
    ExecutionLimits,
    MockProvider,
    ProviderManager,
    ProviderRegistry,
    ProviderRequest,
    ProviderRuntimeExecutionPolicy,
    RateLimiter,
    RetryPolicy,
)


def check(name, ok):
    print(f"{name:<32} {'PASS' if ok else 'FAIL'}")
    assert ok


def main():
    print("NTPE 1.2 Professional Stage-14.3 Provider Runtime Execution Policy Test")
    print("=" * 74)

    provider = MockProvider(name="policy-mock", response_text="translated {prompt}", fail_times=1)
    policy = ProviderRuntimeExecutionPolicy(
        retry_policy=RetryPolicy(max_attempts=2),
        rate_limiter=RateLimiter(max_calls=1000),
        limits=ExecutionLimits(max_total_tokens=1000),
    )
    result = policy.execute(provider, ProviderRequest(prompt="hello"))

    check("Execution Result", result.response.success and result.text == "translated hello")
    check("Retry Applied", result.retry_count == 1 and provider.calls == 2)
    check("Statistics", policy.statistics.snapshot()["success_count"] == 1)
    check("Events", any(e.name == "execution.completed" for e in policy.event_bus.history))
    check("Manifest", policy.manifest()["stage"] == "NTPE 1.2 Professional Stage-14.3")

    registry = ProviderRegistry()
    registry.register(MockProvider(name="manager-mock", response_text="manager {prompt}"), default=True)
    manager = ProviderManager(registry=registry, execution_policy=ProviderRuntimeExecutionPolicy())
    response = manager.complete(ProviderRequest(prompt="bridge"))
    check("Manager Binding", response.text == "manager bridge")
    check("Manager Manifest", "execution_policy" in manager.manifest())

    print("PASS")


if __name__ == "__main__":
    main()
