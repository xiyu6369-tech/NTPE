from __future__ import annotations

from .contracts import ProviderRequest


class RuntimeProviderBridge:
    def __init__(self, manager):
        self.manager = manager

    def execute_prompt(self, prompt: str, model=None, metadata=None):
        return self.manager.complete(ProviderRequest(prompt=prompt, model=model, metadata=metadata or {}))

    def stream_prompt(self, prompt: str, model=None, metadata=None):
        return self.manager.stream(ProviderRequest(prompt=prompt, model=model, metadata=metadata or {}, stream=True))

    def discover_models(self, provider=None):
        return self.manager.registry.discover_models(provider)

    def detect_capabilities(self, provider=None):
        return self.manager.registry.capabilities(provider)

    def health_check(self):
        return self.manager.health()

    def attach_runtime_manifest(self, manifest=None):
        payload = dict(manifest or {})
        payload["ai_provider"] = self.manager.manifest()
        return payload
