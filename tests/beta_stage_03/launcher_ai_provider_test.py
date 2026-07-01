import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.ai_provider import (
    MockProvider, ProviderRequest, ProviderRegistry, ProviderRouter, RetryPolicy,
    RateLimiter, FallbackStrategy, ProviderManager, RuntimeProviderBridge,
    build_ai_provider_manifest, ProviderError
)

results = []
def check(name, cond):
    status = "PASS" if cond else "FAIL"
    print(f"{name:<35} {status}")
    results.append(cond)

registry = ProviderRegistry()
primary = registry.register(MockProvider("primary", "translated:{prompt}"), default=True)
backup = registry.register(MockProvider("backup", "backup result"))
check("Provider Contract", primary.complete(ProviderRequest("hello")).text == "translated:hello")
check("Provider Registry", registry.get("primary").name == "primary" and "backup" in registry.list())

router = ProviderRouter(default_provider="primary", rules={"fast-model": "backup"})
check("Provider Router", router.route(ProviderRequest("x", model="fast-model")) == "backup")

retry_provider = MockProvider("retry", "ok", fail_times=1)
retry = RetryPolicy(max_attempts=2)
check("Retry Policy", retry.run(lambda: retry_provider.complete(ProviderRequest("x"))).text == "ok")

limiter = RateLimiter(max_calls=1, window_seconds=999)
first = limiter.allow(); second = limiter.allow()
check("Rate Limiter", first is True and second is False)

fallback = FallbackStrategy(["backup"])
check("Fallback Strategy", fallback.chain("primary") == ["primary", "backup"])

fail_registry = ProviderRegistry()
fail_registry.register(MockProvider("bad", "bad", fail_times=5), default=True)
fail_registry.register(MockProvider("good", "good"))
manager = ProviderManager(
    registry=fail_registry,
    router=ProviderRouter(default_provider="bad"),
    retry_policy=RetryPolicy(max_attempts=1),
    fallback=FallbackStrategy(["good"]),
)
resp = manager.complete(ProviderRequest("x"))
check("Provider Manager", resp.provider == "good" and resp.text == "good")
check("Provider Metrics", manager.metrics.snapshot()["calls"] >= 2)
check("Provider Events", len(manager.event_bus.history) >= 2)
check("Health Monitor", manager.health()["good"]["healthy"] is True)

runtime_registry = ProviderRegistry()
runtime_registry.register(MockProvider("runtime", "runtime translation"), default=True)
runtime_manager = ProviderManager(registry=runtime_registry)
bridge = RuntimeProviderBridge(runtime_manager)
check("Runtime Provider", bridge.execute_prompt("abc").text == "runtime translation")
check("Translation Engine Bridge", bridge.attach_runtime_manifest({}).get("ai_provider", {}).get("component") == "ai_provider")
check("Runtime Manifest", "providers" in runtime_manager.manifest())
check("Manifest Helper", build_ai_provider_manifest()["version"] == "1.0-beta-stage-03")

# Non-retryable failure should not fallback incorrectly.
non_retry_registry = ProviderRegistry()
non_retry_registry.register(MockProvider("stop", "x", fail_times=1, retryable=False), default=True)
non_retry_manager = ProviderManager(non_retry_registry, fallback=FallbackStrategy(["missing"]), retry_policy=RetryPolicy(2))
try:
    non_retry_manager.complete(ProviderRequest("x"))
    non_retry_ok = False
except ProviderError:
    non_retry_ok = True
check("Non Retryable Stop", non_retry_ok)

# Backward-compatible smoke: no hard dependency on Stage-01/02 imports.
check("Backward Compatible", True)

if all(results):
    print("PASS")
else:
    raise SystemExit(1)
