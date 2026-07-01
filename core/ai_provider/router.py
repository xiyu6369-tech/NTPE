from __future__ import annotations
from typing import Optional, Dict, Any

class ProviderRouter:
    def __init__(self, default_provider: Optional[str] = None, rules: Optional[Dict[str, str]] = None):
        self.default_provider = default_provider
        self.rules = rules or {}
    def route(self, request: Any) -> Optional[str]:
        metadata = getattr(request, "metadata", {}) or {}
        if metadata.get("provider"):
            return metadata["provider"]
        model = getattr(request, "model", None)
        if model and model in self.rules:
            return self.rules[model]
        return self.default_provider
