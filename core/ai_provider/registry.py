from __future__ import annotations
from typing import Dict, List, Optional
from .contracts import AIProvider

class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, AIProvider] = {}
        self._default: Optional[str] = None
    def register(self, provider: AIProvider, default: bool = False):
        self._providers[provider.name] = provider
        if default or self._default is None:
            self._default = provider.name
        return provider
    def get(self, name: Optional[str] = None) -> AIProvider:
        key = name or self._default
        if not key or key not in self._providers:
            raise KeyError(f"provider not registered: {key}")
        return self._providers[key]
    def list(self) -> List[str]:
        return list(self._providers.keys())
    def default_name(self) -> Optional[str]:
        return self._default
