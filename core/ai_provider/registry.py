from __future__ import annotations

from typing import Dict, List, Optional

from .adapters import build_standard_provider_adapters
from .contracts import AIProvider, ModelInfo, ProviderCapability


class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, AIProvider] = {}
        self._default: Optional[str] = None

    def register(self, provider: AIProvider, default: bool = False):
        self._providers[provider.name] = provider
        if default or self._default is None:
            self._default = provider.name
        return provider

    def unregister(self, name: str) -> None:
        self._providers.pop(name, None)
        if self._default == name:
            self._default = next(iter(self._providers), None)

    def get(self, name: Optional[str] = None) -> AIProvider:
        key = name or self._default
        if not key or key not in self._providers:
            raise KeyError(f"provider not registered: {key}")
        return self._providers[key]

    def has(self, name: str) -> bool:
        return name in self._providers

    def list(self) -> List[str]:
        return list(self._providers.keys())

    def default_name(self) -> Optional[str]:
        return self._default

    def set_default(self, name: str) -> None:
        if name not in self._providers:
            raise KeyError(f"provider not registered: {name}")
        self._default = name

    def discover_models(self, provider: Optional[str] = None) -> List[ModelInfo]:
        if provider:
            return self.get(provider).discover_models()
        models: List[ModelInfo] = []
        for item in self._providers.values():
            models.extend(item.discover_models())
        return models

    def capabilities(self, provider: Optional[str] = None) -> Dict[str, ProviderCapability]:
        if provider:
            p = self.get(provider)
            return {p.name: p.detect_capabilities()}
        return {name: p.detect_capabilities() for name, p in self._providers.items()}

    def providers_with_capability(self, capability: str) -> List[str]:
        result: List[str] = []
        for name, cap in self.capabilities().items():
            if bool(getattr(cap, capability, False)):
                result.append(name)
        return result

    def manifest(self) -> Dict[str, object]:
        return {
            "default": self._default,
            "providers": self.list(),
            "models": [m.to_dict() for m in self.discover_models()],
            "capabilities": {k: v.to_dict() for k, v in self.capabilities().items()},
        }


def build_standard_provider_registry(default: str = "nvidia") -> ProviderRegistry:
    registry = ProviderRegistry()
    for name, adapter in build_standard_provider_adapters().items():
        registry.register(adapter, default=(name == default))
    if default not in registry.list():
        registry.set_default(registry.list()[0])
    return registry
