"""Runtime bridge connecting Runtime with Integration Core, CLI, SDK and Plugin surfaces."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .runtime_context import RuntimeContext
from .runtime_dispatcher import RuntimeDispatcher
from .runtime_events import RuntimeEventBridge, RUNTIME_EVENT_COMPLETED, RUNTIME_EVENT_CREATED, RUNTIME_EVENT_FAILED, RUNTIME_EVENT_RESUMED, RUNTIME_EVENT_STARTED, RUNTIME_EVENT_STOPPED
from .runtime_models import RuntimeCommand, RuntimeExecutionResult
from .runtime_registry import RuntimeRegistry


class RuntimeBridge:
    version = "0.8.1"

    def __init__(self, *, registry: Optional[RuntimeRegistry] = None, events: Optional[RuntimeEventBridge] = None) -> None:
        self.registry = registry or RuntimeRegistry()
        self.events = events or RuntimeEventBridge()
        self.dispatcher = RuntimeDispatcher(self.registry)

    def attach(self, runtime: Any, *, name: str = "runtime", metadata: Optional[Dict[str, Any]] = None) -> str:
        item = self.registry.register(runtime, name=name, metadata=metadata)
        self.events.emit(RUNTIME_EVENT_CREATED, runtime_id=item.runtime_id, payload={"metadata": item.to_dict()})
        return item.runtime_id

    def context(self, operation: str, runtime_id: Optional[str] = None, **metadata: Any) -> RuntimeContext:
        return RuntimeContext(operation=operation, runtime_id=runtime_id, metadata=dict(metadata))

    def start(self, runtime_id: str, **payload: Any) -> RuntimeExecutionResult:
        metadata = self.registry.require_metadata(runtime_id)
        metadata.mark("started")
        self.events.emit(RUNTIME_EVENT_STARTED, runtime_id=runtime_id, payload=dict(payload))
        result = self.dispatch(RuntimeCommand("start", runtime_id=runtime_id, payload=dict(payload)))
        if not result.ok and "runtime action unavailable" in str(result.error):
            result = RuntimeExecutionResult.success("start", runtime_id=runtime_id, value={"status": "started"})
        return result

    def stop(self, runtime_id: str, **payload: Any) -> RuntimeExecutionResult:
        metadata = self.registry.require_metadata(runtime_id)
        metadata.mark("stopped")
        self.events.emit(RUNTIME_EVENT_STOPPED, runtime_id=runtime_id, payload=dict(payload))
        result = self.dispatch(RuntimeCommand("stop", runtime_id=runtime_id, payload=dict(payload)))
        if not result.ok and "runtime action unavailable" in str(result.error):
            result = RuntimeExecutionResult.success("stop", runtime_id=runtime_id, value={"status": "stopped"})
        return result

    def resume(self, runtime_id: str, **payload: Any) -> RuntimeExecutionResult:
        metadata = self.registry.require_metadata(runtime_id)
        metadata.mark("resumed")
        self.events.emit(RUNTIME_EVENT_RESUMED, runtime_id=runtime_id, payload=dict(payload))
        return self.dispatch(RuntimeCommand("resume", runtime_id=runtime_id, payload=dict(payload)))

    def execute(self, runtime_id: str, action: str = "execute", **payload: Any) -> RuntimeExecutionResult:
        result = self.dispatch(RuntimeCommand(action=action, runtime_id=runtime_id, payload=dict(payload)))
        if result.ok:
            self.registry.require_metadata(runtime_id).mark("completed")
            self.events.emit(RUNTIME_EVENT_COMPLETED, runtime_id=runtime_id, payload=result.to_dict())
        else:
            self.registry.require_metadata(runtime_id).mark("failed")
            self.events.emit(RUNTIME_EVENT_FAILED, runtime_id=runtime_id, payload=result.to_dict())
        return result

    def dispatch(self, command: RuntimeCommand) -> RuntimeExecutionResult:
        return self.dispatcher.dispatch(command)

    def manifest(self) -> Dict[str, Any]:
        return {"version": self.version, "registry": self.registry.manifest(), "events": self.events.manifest()}
