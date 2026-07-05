import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.ai_provider import (
    ProviderCapability,
    ProviderManager,
    ProviderRequest,
    ProviderRouter,
    RateLimiter,
    RuntimeProviderBridge,
    build_ai_provider_manifest,
    build_standard_provider_registry,
)

results = []


def check(name, cond):
    status = "PASS" if cond else "FAIL"
    print(f"{name:<38} {status}")
    results.append(cond)


registry = build_standard_provider_registry(default="nvidia")
expected = {"nvidia", "openai", "gemini", "anthropic", "ollama", "openrouter", "custom"}
check("Standard Providers", expected.issubset(set(registry.list())))
check("Default Provider", registry.default_name() == "nvidia")

models = registry.discover_models()
check("Model Discovery", len(models) >= 7 and any(m.id == "meta/llama-3.3-70b-instruct" for m in models))

capabilities = registry.capabilities()
check("Capability Detection", isinstance(capabilities["nvidia"], ProviderCapability) and capabilities["nvidia"].streaming)
check("Streaming Provider Filter", "ollama" in registry.providers_with_capability("streaming"))

router = ProviderRouter(default_provider="nvidia", rules={"gemini-2.5-flash": "gemini"})
manager = ProviderManager(registry=registry, router=router, rate_limiter=RateLimiter(max_calls=1000))
response = manager.complete(ProviderRequest("Translate this", model="gemini-2.5-flash"))
check("Provider Adapter", response.provider == "gemini" and response.model == "gemini-2.5-flash")
check("Token Usage", response.usage.total_tokens > 0)
check("Cost Statistics", response.cost.currency == "USD")

chunks = list(manager.stream(ProviderRequest("stream me", metadata={"provider": "custom"})))
check("Streaming", len(chunks) == 1 and chunks[0].done and chunks[0].provider == "custom")

health = manager.health()
check("Health Check", health["nvidia"]["healthy"] and "models" in health["nvidia"])

bridge = RuntimeProviderBridge(manager)
check("Runtime Bridge Discovery", len(bridge.discover_models("openai")) >= 1)
check("Runtime Bridge Health", bridge.health_check()["openai"]["healthy"])
attached = bridge.attach_runtime_manifest({"runtime": "translation"})
check("Runtime Manifest Attach", attached["ai_provider"]["stage"] == "NTPE 1.2 Professional Stage-14")

manifest = build_ai_provider_manifest()
check("Stage Manifest", manifest["framework_version"] == "1.2-professional-stage-14")
check("Backward Compatibility", callable(manager.complete) and callable(bridge.execute_prompt))

if all(results):
    print("PASS")
else:
    raise SystemExit(1)
