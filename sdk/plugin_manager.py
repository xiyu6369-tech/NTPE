"""Stage-07.7 SDK Plugin manager and lifecycle bridge."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .plugin import SDKPlugin
from .plugin_context import SDKPluginContext
from .plugin_loader import SDKPluginLoader
from .plugin_manifest import PluginManifest
from .plugin_models import PluginDescriptor, PluginResult
from .plugin_registry import SDKPluginRegistry


class SDKPluginManager:
    def __init__(self, registry: Optional[SDKPluginRegistry] = None, loader: Optional[SDKPluginLoader] = None, context: Optional[SDKPluginContext] = None) -> None:
        self.registry = registry or SDKPluginRegistry()
        self.loader = loader or SDKPluginLoader()
        self.context = context or SDKPluginContext(metadata={"stage": "Stage-07.7"})

    def register(self, plugin: SDKPlugin, *, replace: bool = False) -> SDKPlugin:
        registered = self.registry.register(plugin, replace=replace)
        self.context.emit("plugin.registered", plugin=plugin.manifest.name)
        return registered

    def load(self, manifest: PluginManifest) -> SDKPlugin:
        plugin = self.loader.from_manifest(manifest)
        self.register(plugin, replace=True)
        plugin.load(self.context)
        return plugin

    def initialize(self, name: str) -> PluginResult:
        return self.registry.require(name).initialize(self.context)

    def execute(self, name: str, **kwargs: Any) -> PluginResult:
        plugin = self.registry.require(name)
        if not plugin.loaded:
            plugin.load(self.context)
        if not plugin.initialized:
            plugin.initialize(self.context)
        try:
            return plugin.execute(self.context, **kwargs)
        except Exception as exc:  # lifecycle errors must be isolated
            self.context.emit("plugin.error", plugin=name, error=str(exc))
            return PluginResult(name, status="error", error=str(exc), metadata={"isolated": True})

    def unload(self, name: str) -> PluginResult:
        return self.registry.require(name).unload(self.context)

    def discover(self, capability: Optional[str] = None) -> List[PluginDescriptor]:
        return self.registry.discover(capability)

    def runtime_bridge(self) -> Dict[str, Any]:
        bridge = self.context.to_runtime_bridge()
        bridge.update({"plugins": [item.to_dict() for item in self.registry.list()], "stage": "Stage-07.7"})
        return bridge
