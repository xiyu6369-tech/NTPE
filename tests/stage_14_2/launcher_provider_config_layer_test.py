import os
import sys
import tempfile
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.ai_provider import (
    ProviderConfigLayer,
    ProviderCredential,
    ProviderCredentialRegistry,
    ProviderManager,
    ProviderRequest,
    mask_mapping,
    mask_secret,
)
from core.translation_runtime import TranslationRuntime

results = []


def check(name, cond):
    status = "PASS" if cond else "FAIL"
    print(f"{name:<44} {status}")
    results.append(cond)


check("Secret Mask", mask_secret("abcd123456") == "******3456")
check("Mapping Mask", mask_mapping({"api_key": "secret-key", "safe": "ok"})["api_key"].endswith("-key"))

creds = ProviderCredentialRegistry()
creds.register(ProviderCredential(provider="nvidia", env_var="NTPE_TEST_KEY"))
check("Credential Env Resolve", creds.resolve_api_key("nvidia", {"NTPE_TEST_KEY": "abc123"}) == "abc123")
check("Credential Validation", creds.validate("nvidia", {"NTPE_TEST_KEY": "abc123"})["configured"] is True)

layer = ProviderConfigLayer.standard(default_provider="openai")
check("Standard Config Profiles", {"nvidia", "openai", "gemini", "anthropic", "ollama", "openrouter", "custom"}.issubset(layer.profiles))
check("Default Config Provider", layer.default_provider == "openai")

payload = {
    "default_provider": "gemini",
    "retry_defaults": {"max_attempts": 4, "base_delay_seconds": 0.0, "backoff_factor": 1.5},
    "rate_limit_defaults": {"max_calls": 99, "window_seconds": 60},
    "providers": {
        "gemini": {"env_var": "NTPE_TEST_GEMINI", "default_model": "gemini-test"},
        "openai": {"enabled": False},
        "custom": {"api_key": "plain-secret", "metadata": {"token": "nested-secret"}},
    },
}
loaded = ProviderConfigLayer.from_dict(payload)
check("Config Override", loaded.default_provider == "gemini" and loaded.profiles["gemini"].default_model == "gemini-test")
check("Config Disable Provider", "openai" not in loaded.enabled_profiles())
check("Config Credential Mask", loaded.masked_manifest()["providers"]["custom"]["api_key"].endswith("cret"))
check("Credential Local Valid", loaded.validate_credentials()["custom"]["configured"] is True)

registry = loaded.build_registry()
manager = ProviderManager(registry=registry, config_layer=loaded)
response = manager.complete(ProviderRequest("config layer", metadata={"provider": "gemini"}))
check("Manager Config Binding", response.provider == "gemini" and response.model == "gemini-test")
check("Manager Manifest Config", manager.manifest()["config"]["default_provider"] == "gemini")

runtime = TranslationRuntime(root=ROOT)
config_manifest = runtime.provider_config_manifest()
check("Runtime Config Manifest", config_manifest["status"] == "success" and "nvidia" in config_manifest["config"]["providers"])
credential_status = runtime.validate_provider_credentials()
check("Runtime Credential Validation", credential_status["status"] == "success" and "nvidia" in credential_status["credentials"])

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "provider_config.template.json"
    saved = runtime.save_provider_config_template(path)
    check("Runtime Config Template", Path(saved["path"]).exists())

if all(results):
    print("PASS")
else:
    raise SystemExit(1)
