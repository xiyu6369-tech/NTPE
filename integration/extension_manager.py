"""Extension manager for NTPE Stage-08.4."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .extension_context import ExtensionContext
from .extension_dispatcher import ExtensionDispatcher
from .extension_events import (
    EXTENSION_EVENT_DISABLED,
    EXTENSION_EVENT_DISCOVERED,
    EXTENSION_EVENT_ENABLED,
    EXTENSION_EVENT_EXECUTED,
    EXTENSION_EVENT_FAILED,
    EXTENSION_EVENT_INITIALIZED,
    EXTENSION_EVENT_LOADED,
    EXTENSION_EVENT_REGISTERED,
    EXTENSION_EVENT_UNLOADED,
    ExtensionEventBus,
)
from .extension_loader import ExtensionLoader
from .extension_models import EXTENSION_FRAMEWORK_STAGE, EXTENSION_FRAMEWORK_VERSION, ExtensionCommand, ExtensionManifest, ExtensionResult
from .extension_registry import ExtensionRegistry


class ExtensionManager:
    version = EXTENSION_FRAMEWORK_VERSION
    stage = EXTENSION_FRAMEWORK_STAGE

    def __init__(self, *, registry: Optional[ExtensionRegistry] = None, events: Optional[ExtensionEventBus] = None, loader: Optional[ExtensionLoader] = None, runtime: Any = None, sdk: Any = None, cli: Any = None, plugin_manager: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        self.registry = registry or ExtensionRegistry()
        self.events = events or ExtensionEventBus()
        self.loader = loader or ExtensionLoader()
        self.dispatcher = ExtensionDispatcher(self.registry)
        self.runtime = runtime
        self.sdk = sdk
        self.cli = cli
        self.plugin_manager = plugin_manager
        self.config = dict(config or {})

    def attach_runtime(self, runtime: Any) -> None:
        self.runtime = runtime

    def attach_sdk(self, sdk: Any) -> None:
        self.sdk = sdk

    def attach_cli(self, cli: Any) -> None:
        self.cli = cli

    def attach_plugin_manager(self, plugin_manager: Any) -> None:
        self.plugin_manager = plugin_manager

    def register(self, extension: Any, *, manifest: ExtensionManifest | Dict[str, Any] | None = None, name: Optional[str] = None, source: str = "integration", replace: bool = False, metadata: Optional[Dict[str, Any]] = None) -> str:
        descriptor = self.registry.register(extension, manifest=manifest, name=name, source=source, replace=replace, metadata=metadata)
        self.events.emit(EXTENSION_EVENT_REGISTERED, extension_name=descriptor.name, payload={"descriptor": descriptor.to_dict()}, source=source)
        return descriptor.name

    def load_manifest(self, manifest: ExtensionManifest | Dict[str, Any], *, replace: bool = False, source: str = "manifest") -> str:
        extension = self.loader.load_from_manifest(manifest)
        return self.register(extension, manifest=manifest, source=source, replace=replace)

    def context(self, operation: str, *, extension_name: Optional[str] = None, session_id: Optional[str] = None, **metadata: Any) -> ExtensionContext:
        return ExtensionContext(operation=operation, extension_name=extension_name, runtime=self.runtime, sdk=self.sdk, cli=self.cli, plugin_manager=self.plugin_manager, config=dict(self.config), session_id=session_id, metadata=dict(metadata))

    def load(self, extension_name: str, **payload: Any) -> ExtensionResult:
        return self._emit_result(extension_name, "load", EXTENSION_EVENT_LOADED, payload)

    def initialize(self, extension_name: str, **payload: Any) -> ExtensionResult:
        return self._emit_result(extension_name, "initialize", EXTENSION_EVENT_INITIALIZED, payload)

    def enable(self, extension_name: str, **payload: Any) -> ExtensionResult:
        return self._emit_result(extension_name, "enable", EXTENSION_EVENT_ENABLED, payload)

    def disable(self, extension_name: str, **payload: Any) -> ExtensionResult:
        return self._emit_result(extension_name, "disable", EXTENSION_EVENT_DISABLED, payload)

    def execute(self, extension_name: str, **payload: Any) -> ExtensionResult:
        return self._emit_result(extension_name, "execute", EXTENSION_EVENT_EXECUTED, payload)

    def unload(self, extension_name: str, **payload: Any) -> ExtensionResult:
        return self._emit_result(extension_name, "unload", EXTENSION_EVENT_UNLOADED, payload)

    def lifecycle(self, extension_name: str, *, session_id: Optional[str] = None) -> Dict[str, ExtensionResult]:
        return {
            "load": self.load(extension_name, session_id=session_id),
            "initialize": self.initialize(extension_name, session_id=session_id),
            "enable": self.enable(extension_name, session_id=session_id),
        }

    def discover(self, capability: Optional[str] = None) -> list[dict]:
        items = [item.to_dict() for item in self.registry.discover(capability)]
        self.events.emit(EXTENSION_EVENT_DISCOVERED, payload={"capability": capability, "count": len(items)})
        return items

    def _emit_result(self, extension_name: str, action: str, event_type: str, payload: Dict[str, Any]) -> ExtensionResult:
        result = self._dispatch(extension_name, action, payload)
        self.events.emit(event_type if result.ok else EXTENSION_EVENT_FAILED, extension_name=extension_name, payload=result.to_dict(), correlation_id=result.metadata.get("correlation_id"))
        return result

    def _dispatch(self, extension_name: str, action: str, payload: Dict[str, Any]) -> ExtensionResult:
        session_id = payload.pop("session_id", None)
        context = self.context(f"extension.{action}", extension_name=extension_name, session_id=session_id)
        command = ExtensionCommand(extension_name=extension_name, action=action, payload=dict(payload), session_id=session_id, correlation_id=context.correlation_id)
        return self.dispatcher.dispatch(command, context)

    def bridge_status(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "runtime_attached": self.runtime is not None,
            "sdk_attached": self.sdk is not None,
            "cli_attached": self.cli is not None,
            "plugin_manager_attached": self.plugin_manager is not None,
            "registry": self.registry.manifest(),
        }

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "registry": self.registry.manifest(),
            "events": self.events.manifest(),
            "loader": self.loader.manifest(),
            "bridge": self.bridge_status(),
            "config": dict(self.config),
        }
