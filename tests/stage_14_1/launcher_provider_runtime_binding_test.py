import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.ai_provider import MockProvider, ProviderManager, ProviderRouter, build_standard_provider_registry
from core.translation_runtime import TranslationRuntime

results = []


def check(name, cond):
    status = "PASS" if cond else "FAIL"
    print(f"{name:<42} {status}")
    results.append(cond)


runtime = TranslationRuntime(root=ROOT)
contract = runtime.validate_compatibility()
check("Runtime Compatibility", contract["status"] == "success")
check("Runtime Version", runtime.version in {"1.2-professional-stage-14.1", "1.2-professional-stage-14.2"})

manifest = runtime.describe()
check("Provider Manifest Attached", manifest["ai_provider"]["stage"] == "NTPE 1.2 Professional Stage-14")
check("Provider Capability Declared", any(c["name"] == "provider_runtime_binding" for c in manifest["capabilities"]))

models = runtime.discover_provider_models("nvidia")
check("Runtime Model Discovery", models["status"] == "success" and models["models"][0]["provider"] == "nvidia")

capabilities = runtime.detect_provider_capabilities("openai")
check("Runtime Capability Detection", capabilities["capabilities"]["openai"]["streaming"] is True)

response = runtime.complete_provider_prompt("Translate stage binding", metadata={"provider": "gemini"})
check("Runtime Completion Binding", response["provider"] == "gemini" and response["usage"]["total_tokens"] > 0)

chunks = runtime.stream_provider_prompt("Stream stage binding", metadata={"provider": "custom"})
check("Runtime Streaming Binding", len(chunks) == 1 and chunks[0]["provider"] == "custom" and chunks[0]["done"] is True)

health = runtime.provider_health_check()
check("Runtime Health Binding", health["status"] == "success" and health["health"]["nvidia"]["healthy"] is True)

registry = build_standard_provider_registry(default="custom")
manager = ProviderManager(registry=registry, router=ProviderRouter())
manager.registry.register(MockProvider(name="mock_runtime", response_text="bound:{prompt}"), default=True)
bind = runtime.bind_ai_provider_manager(manager)
check("External Manager Binding", bind["default_provider"] == "mock_runtime")

custom_response = runtime.complete_provider_prompt("OK")
check("Bound Manager Completion", custom_response["provider"] == "mock_runtime" and custom_response["text"] == "bound:OK")

runtime.register_ai_provider(MockProvider(name="second_mock", response_text="second"), default=True)
check("Runtime Provider Register", runtime.provider_manifest()["registry"]["default"] == "second_mock")

if all(results):
    print("PASS")
else:
    raise SystemExit(1)
