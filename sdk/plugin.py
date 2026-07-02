"""Stage-07.7 SDK Plugin base interface."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .plugin_context import SDKPluginContext
from .plugin_manifest import PluginManifest
from .plugin_models import PluginDescriptor, PluginResult


class SDKPlugin:
    name = "sdk-plugin"
    version = "1.0.0"
    capabilities = []

    def __init__(self, manifest: Optional[PluginManifest] = None, **metadata: Any) -> None:
        self.manifest = manifest or PluginManifest(
            name=self.name,
            version=self.version,
            capabilities=list(self.capabilities),
            metadata=dict(metadata),
        )
        self.initialized = False
        self.loaded = False
        self.metadata: Dict[str, Any] = dict(metadata)

    def descriptor(self) -> PluginDescriptor:
        return PluginDescriptor(
            name=self.manifest.name,
            version=self.manifest.version,
            stage="Stage-07.7",
            enabled=True,
            capabilities=list(self.manifest.capabilities),
            metadata=dict(self.manifest.metadata),
        )

    def load(self, context: Optional[SDKPluginContext] = None) -> PluginResult:
        self.loaded = True
        if context:
            context.emit("plugin.loaded", plugin=self.manifest.name)
        return PluginResult(self.manifest.name, metadata={"loaded": True})

    def initialize(self, context: Optional[SDKPluginContext] = None) -> PluginResult:
        self.initialized = True
        if context:
            context.emit("plugin.initialized", plugin=self.manifest.name)
        return PluginResult(self.manifest.name, metadata={"initialized": True})

    def execute(self, context: Optional[SDKPluginContext] = None, **kwargs: Any) -> PluginResult:
        if context:
            context.emit("plugin.executed", plugin=self.manifest.name, kwargs=dict(kwargs))
        return PluginResult(self.manifest.name, output=dict(kwargs), metadata={"executed": True})

    def unload(self, context: Optional[SDKPluginContext] = None) -> PluginResult:
        self.loaded = False
        self.initialized = False
        if context:
            context.emit("plugin.unloaded", plugin=self.manifest.name)
        return PluginResult(self.manifest.name, metadata={"unloaded": True})
