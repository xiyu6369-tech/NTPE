"""Runtime command dispatcher for NTPE Stage-08.1."""
from __future__ import annotations

from typing import Any, Optional

from .runtime_models import RuntimeCommand, RuntimeExecutionResult
from .runtime_registry import RuntimeRegistry


class RuntimeDispatcher:
    def __init__(self, registry: RuntimeRegistry) -> None:
        self.registry = registry

    def dispatch(self, command: RuntimeCommand | str, *, runtime_id: Optional[str] = None, **payload: Any) -> RuntimeExecutionResult:
        if isinstance(command, str):
            command = RuntimeCommand(action=command, runtime_id=runtime_id, payload=dict(payload))
        try:
            target_id = command.runtime_id or runtime_id
            if not target_id:
                raise RuntimeError("runtime_id is required")
            runtime = self.registry.require(target_id)
            action = command.action
            if hasattr(runtime, action):
                value = getattr(runtime, action)(**command.payload)
            elif callable(runtime):
                value = runtime(action=action, **command.payload)
            else:
                raise AttributeError(f"runtime action unavailable: {action}")
            return RuntimeExecutionResult.success(action, runtime_id=target_id, value=value)
        except Exception as exc:
            return RuntimeExecutionResult.failure(command.action if isinstance(command, RuntimeCommand) else str(command), str(exc), runtime_id=runtime_id)
