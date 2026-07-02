"""Plugin integration manager for NTPE Stage-08.3."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .plugin_bridge import PluginIntegrationBridge
from .plugin_models import PluginIntegrationResult


class PluginIntegrationManager:
    version = "0.8.3"

    def __init__(self, *, bridge: Optional[PluginIntegrationBridge] = None) -> None:
        self.bridge = bridge or PluginIntegrationBridge()

    def attach_runtime(self, runtime: Any) -> None:
        self.bridge.attach_runtime(runtime)

    def attach_sdk(self, sdk: Any) -> None:
        self.bridge.attach_sdk(sdk)

    def attach_cli(self, cli: Any) -> None:
        self.bridge.attach_cli(cli)

    def register(self, plugin: Any, **kwargs: Any) -> str:
        return self.bridge.register(plugin, **kwargs)

    def load(self, name: str, **payload: Any) -> PluginIntegrationResult:
        return self.bridge.load(name, **payload)

    def initialize(self, name: str, **payload: Any) -> PluginIntegrationResult:
        return self.bridge.initialize(name, **payload)

    def execute(self, name: str, **payload: Any) -> PluginIntegrationResult:
        return self.bridge.execute(name, **payload)

    def unload(self, name: str, **payload: Any) -> PluginIntegrationResult:
        return self.bridge.unload(name, **payload)

    def discover(self, capability: Optional[str] = None) -> list[dict]:
        return self.bridge.discover(capability)

    def manifest(self) -> Dict[str, Any]:
        manifest = self.bridge.manifest()
        manifest["manager_version"] = self.version
        return manifest
