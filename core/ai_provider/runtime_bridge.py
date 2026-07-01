from __future__ import annotations
from .contracts import ProviderRequest

class RuntimeProviderBridge:
    def __init__(self, manager):
        self.manager = manager
    def execute_prompt(self, prompt: str, model=None, metadata=None):
        return self.manager.complete(ProviderRequest(prompt=prompt, model=model, metadata=metadata or {}))
    def attach_runtime_manifest(self, manifest=None):
        payload = dict(manifest or {})
        payload["ai_provider"] = self.manager.manifest()
        return payload
