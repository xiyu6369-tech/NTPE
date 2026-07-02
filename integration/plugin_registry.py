"""Plugin registry for integration layer."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .plugin_models import IntegratedPluginDescriptor


class PluginIntegrationRegistry:
    version = "0.8.3"

    def __init__(self) -> None:
        self._plugins: Dict[str, Any] = {}
        self._descriptors: Dict[str, IntegratedPluginDescriptor] = {}

    def register(self, plugin: Any, *, name: Optional[str] = None, source: str = "sdk", replace: bool = False, metadata: Optional[Dict[str, Any]] = None) -> IntegratedPluginDescriptor:
        manifest = getattr(plugin, "manifest", None)
        plugin_name = name or getattr(manifest, "name", None) or getattr(plugin, "name", plugin.__class__.__name__)
        if plugin_name in self._plugins and not replace:
            raise ValueError(f"plugin already registered: {plugin_name}")
        capabilities = list(getattr(manifest, "capabilities", getattr(plugin, "capabilities", [])) or [])
        version = str(getattr(manifest, "version", getattr(plugin, "version", "1.0.0")))
        descriptor = IntegratedPluginDescriptor(plugin_name, version=version, source=source, capabilities=capabilities, metadata=dict(metadata or {}))
        self._plugins[plugin_name] = plugin
        self._descriptors[plugin_name] = descriptor
        return descriptor

    def unregister(self, name: str) -> Optional[Any]:
        self._descriptors.pop(name, None)
        return self._plugins.pop(name, None)

    def get(self, name: str) -> Optional[Any]:
        return self._plugins.get(name)

    def require(self, name: str) -> Any:
        plugin = self.get(name)
        if plugin is None:
            raise KeyError(f"plugin not registered: {name}")
        return plugin

    def descriptor(self, name: str) -> IntegratedPluginDescriptor:
        if name not in self._descriptors:
            raise KeyError(f"plugin descriptor not registered: {name}")
        return self._descriptors[name]

    def names(self) -> List[str]:
        return sorted(self._plugins.keys())

    def discover(self, capability: Optional[str] = None) -> List[IntegratedPluginDescriptor]:
        values = list(self._descriptors.values())
        if capability is None:
            return values
        return [item for item in values if capability in item.capabilities]

    def mark(self, name: str, status: str) -> None:
        self.descriptor(name).mark(status)

    def manifest(self) -> Dict[str, Any]:
        return {"version": self.version, "count": len(self._descriptors), "plugins": [item.to_dict() for item in self.discover()]}

    def __iter__(self) -> Iterable[Any]:
        return iter(self._plugins.values())
