"""SDK-CLI bridge for NTPE Stage-08.2."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .bridge_context import BridgeContext
from .bridge_dispatcher import BridgeDispatcher
from .bridge_events import BRIDGE_EVENT_COMMAND, BRIDGE_EVENT_COMPLETED, BRIDGE_EVENT_FAILED, BRIDGE_EVENT_REGISTERED, BridgeEventBus
from .bridge_models import BRIDGE_INTEGRATION_STAGE, BRIDGE_INTEGRATION_VERSION, BridgeCommand, BridgeResult
from .bridge_registry import BridgeRegistry


class SDKCLIBridge:
    """A thin shared bridge between SDK and CLI surfaces.

    It does not replace the existing CLI or SDK contracts. It normalizes command
    routing, shared session/configuration metadata, and event propagation while
    delegating actual work to registered endpoints.
    """

    version = BRIDGE_INTEGRATION_VERSION
    stage = BRIDGE_INTEGRATION_STAGE

    def __init__(self, *, registry: Optional[BridgeRegistry] = None, events: Optional[BridgeEventBus] = None, configuration: Optional[Dict[str, Any]] = None) -> None:
        self.registry = registry or BridgeRegistry()
        self.events = events or BridgeEventBus()
        self.dispatcher = BridgeDispatcher(self.registry)
        self.configuration = dict(configuration or {})
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def register_sdk(self, sdk_client: Any, *, name: str = "sdk", metadata: Optional[Dict[str, Any]] = None) -> str:
        return self._register(name, "sdk", sdk_client, metadata=metadata)

    def register_cli(self, cli_adapter: Any, *, name: str = "cli", metadata: Optional[Dict[str, Any]] = None) -> str:
        return self._register(name, "cli", cli_adapter, metadata=metadata)

    def register_runtime(self, runtime: Any, *, name: str = "runtime", metadata: Optional[Dict[str, Any]] = None) -> str:
        return self._register(name, "runtime", runtime, metadata=metadata)

    def _register(self, name: str, kind: str, instance: Any, *, metadata: Optional[Dict[str, Any]] = None) -> str:
        endpoint = self.registry.register(name, kind, instance, version=str(getattr(instance, "version", "1.0")), metadata=dict(metadata or {}))
        self.events.emit(BRIDGE_EVENT_REGISTERED, surface=kind, payload={"endpoint": endpoint.to_dict()})
        return endpoint.name

    def create_session(self, session_id: str, **metadata: Any) -> Dict[str, Any]:
        record = {"session_id": session_id, "configuration": dict(self.configuration), "metadata": dict(metadata)}
        self.sessions[session_id] = record
        return dict(record)

    def context(self, operation: str, *, surface: str = "bridge", session_id: Optional[str] = None, runtime_id: Optional[str] = None, **metadata: Any) -> BridgeContext:
        config = dict(self.configuration)
        if session_id and session_id in self.sessions:
            config.update(self.sessions[session_id].get("configuration", {}))
        return BridgeContext(operation=operation, surface=surface, session_id=session_id, runtime_id=runtime_id, configuration=config, metadata=dict(metadata))

    def route(self, surface: str, action: str, **payload: Any) -> BridgeResult:
        context = self.context(f"{surface}.{action}", surface=surface, session_id=payload.pop("session_id", None), runtime_id=payload.get("runtime_id"))
        command = BridgeCommand(surface=surface, action=action, payload=dict(payload), session_id=context.session_id, correlation_id=context.correlation_id)
        self.events.emit(BRIDGE_EVENT_COMMAND, surface=surface, payload=command.to_dict(), correlation_id=context.correlation_id)
        result = self.dispatcher.dispatch(command)
        event_type = BRIDGE_EVENT_COMPLETED if result.ok else BRIDGE_EVENT_FAILED
        self.events.emit(event_type, surface=surface, payload=result.to_dict(), correlation_id=context.correlation_id)
        return result

    def sdk_to_cli(self, action: str, **payload: Any) -> BridgeResult:
        return self.route("cli", action, **payload)

    def cli_to_sdk(self, action: str, **payload: Any) -> BridgeResult:
        return self.route("sdk", action, **payload)

    def shared_configuration(self) -> Dict[str, Any]:
        return dict(self.configuration)

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "registry": self.registry.manifest(),
            "events": self.events.manifest(),
            "sessions": sorted(self.sessions),
            "configuration": dict(self.configuration),
        }
