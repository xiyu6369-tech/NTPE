"""Stage-07.7 SDK Plugin registry."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from .plugin import SDKPlugin
from .plugin_models import PluginDescriptor


class SDKPluginRegistry:
    def __init__(self) -> None:
        self._plugins: Dict[str, SDKPlugin] = {}

    def register(self, plugin: SDKPlugin, *, replace: bool = False) -> SDKPlugin:
        name = plugin.manifest.name
        if name in self._plugins and not replace:
            raise ValueError(f"Plugin already registered: {name}")
        self._plugins[name] = plugin
        return plugin

    def unregister(self, name: str) -> Optional[SDKPlugin]:
        return self._plugins.pop(name, None)

    def get(self, name: str) -> Optional[SDKPlugin]:
        return self._plugins.get(name)

    def require(self, name: str) -> SDKPlugin:
        plugin = self.get(name)
        if plugin is None:
            raise KeyError(f"Plugin not registered: {name}")
        return plugin

    def names(self) -> List[str]:
        return sorted(self._plugins.keys())

    def list(self) -> List[PluginDescriptor]:
        return [plugin.descriptor() for plugin in self._plugins.values()]

    def discover(self, capability: Optional[str] = None) -> List[PluginDescriptor]:
        descriptors = self.list()
        if capability is None:
            return descriptors
        return [item for item in descriptors if capability in item.capabilities]

    def __iter__(self) -> Iterable[SDKPlugin]:
        return iter(self._plugins.values())
