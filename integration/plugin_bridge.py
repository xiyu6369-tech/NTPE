"""Plugin integration bridge for NTPE Stage-08.3."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .plugin_context import PluginIntegrationContext
from .plugin_dispatcher import PluginDispatcher
from .plugin_events import (
    PLUGIN_EVENT_DISCOVERED,
    PLUGIN_EVENT_EXECUTED,
    PLUGIN_EVENT_FAILED,
    PLUGIN_EVENT_INITIALIZED,
    PLUGIN_EVENT_LOADED,
    PLUGIN_EVENT_REGISTERED,
    PLUGIN_EVENT_UNLOADED,
    PluginEventBus,
)
from .plugin_models import PLUGIN_INTEGRATION_STAGE, PLUGIN_INTEGRATION_VERSION, PluginCommand, PluginIntegrationResult
from .plugin_registry import PluginIntegrationRegistry


class PluginIntegrationBridge:
    version = PLUGIN_INTEGRATION_VERSION
    stage = PLUGIN_INTEGRATION_STAGE

    def __init__(self, *, registry: Optional[PluginIntegrationRegistry] = None, events: Optional[PluginEventBus] = None, runtime: Any = None, sdk: Any = None, cli: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        self.registry = registry or PluginIntegrationRegistry()
        self.events = events or PluginEventBus()
        self.dispatcher = PluginDispatcher(self.registry)
        self.runtime = runtime
        self.sdk = sdk
        self.cli = cli
        self.config = dict(config or {})

    def attach_runtime(self, runtime: Any) -> None:
        self.runtime = runtime

    def attach_sdk(self, sdk: Any) -> None:
        self.sdk = sdk

    def attach_cli(self, cli: Any) -> None:
        self.cli = cli

    def register(self, plugin: Any, *, name: Optional[str] = None, source: str = "sdk", replace: bool = False, metadata: Optional[Dict[str, Any]] = None) -> str:
        descriptor = self.registry.register(plugin, name=name, source=source, replace=replace, metadata=metadata)
        self.events.emit(PLUGIN_EVENT_REGISTERED, plugin_name=descriptor.name, payload={"descriptor": descriptor.to_dict()}, source=source)
        return descriptor.name

    def context(self, operation: str, *, plugin_name: Optional[str] = None, session_id: Optional[str] = None, **metadata: Any) -> PluginIntegrationContext:
        return PluginIntegrationContext(
            operation=operation,
            plugin_name=plugin_name,
            runtime=self.runtime,
            sdk=self.sdk,
            cli=self.cli,
            config=dict(self.config),
            session_id=session_id,
            metadata=dict(metadata),
        )

    def lifecycle(self, plugin_name: str, *, session_id: Optional[str] = None) -> Dict[str, PluginIntegrationResult]:
        return {
            "load": self.load(plugin_name, session_id=session_id),
            "initialize": self.initialize(plugin_name, session_id=session_id),
        }

    def load(self, plugin_name: str, **payload: Any) -> PluginIntegrationResult:
        result = self._dispatch(plugin_name, "load", payload)
        self.events.emit(PLUGIN_EVENT_LOADED if result.ok else PLUGIN_EVENT_FAILED, plugin_name=plugin_name, payload=result.to_dict(), correlation_id=result.metadata.get("correlation_id"))
        return result

    def initialize(self, plugin_name: str, **payload: Any) -> PluginIntegrationResult:
        result = self._dispatch(plugin_name, "initialize", payload)
        self.events.emit(PLUGIN_EVENT_INITIALIZED if result.ok else PLUGIN_EVENT_FAILED, plugin_name=plugin_name, payload=result.to_dict(), correlation_id=result.metadata.get("correlation_id"))
        return result

    def execute(self, plugin_name: str, **payload: Any) -> PluginIntegrationResult:
        if hasattr(self.registry.require(plugin_name), "loaded") and not getattr(self.registry.require(plugin_name), "loaded"):
            self.load(plugin_name)
        if hasattr(self.registry.require(plugin_name), "initialized") and not getattr(self.registry.require(plugin_name), "initialized"):
            self.initialize(plugin_name)
        result = self._dispatch(plugin_name, "execute", payload)
        self.events.emit(PLUGIN_EVENT_EXECUTED if result.ok else PLUGIN_EVENT_FAILED, plugin_name=plugin_name, payload=result.to_dict(), correlation_id=result.metadata.get("correlation_id"))
        return result

    def unload(self, plugin_name: str, **payload: Any) -> PluginIntegrationResult:
        result = self._dispatch(plugin_name, "unload", payload)
        self.events.emit(PLUGIN_EVENT_UNLOADED if result.ok else PLUGIN_EVENT_FAILED, plugin_name=plugin_name, payload=result.to_dict(), correlation_id=result.metadata.get("correlation_id"))
        return result

    def discover(self, capability: Optional[str] = None) -> list[dict]:
        items = [item.to_dict() for item in self.registry.discover(capability)]
        self.events.emit(PLUGIN_EVENT_DISCOVERED, payload={"capability": capability, "count": len(items)})
        return items

    def _dispatch(self, plugin_name: str, action: str, payload: Dict[str, Any]) -> PluginIntegrationResult:
        session_id = payload.pop("session_id", None)
        context = self.context(f"plugin.{action}", plugin_name=plugin_name, session_id=session_id)
        command = PluginCommand(plugin_name=plugin_name, action=action, payload=dict(payload), session_id=session_id, correlation_id=context.correlation_id)
        return self.dispatcher.dispatch(command, context)

    def runtime_bridge(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "runtime_attached": self.runtime is not None,
            "sdk_attached": self.sdk is not None,
            "cli_attached": self.cli is not None,
            "registry": self.registry.manifest(),
        }

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "registry": self.registry.manifest(),
            "events": self.events.manifest(),
            "runtime_bridge": self.runtime_bridge(),
            "config": dict(self.config),
        }
