"""Service lifecycle hooks for NTPE 1.0 Beta Stage-10.6.

This module is additive to Platform Services. It provides a small,
dependency-free hook registry that can be used by future CLI, SDK, service
host, and platform layers without changing frozen Foundation, Integration, or
Workflow contracts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from time import perf_counter
from typing import Any, Callable, Dict, Iterable, List, Optional
from uuid import uuid4

PLATFORM_LIFECYCLE_VERSION = "1.0.0-beta.10.6"
PLATFORM_LIFECYCLE_STAGE = "10.6"

LifecycleHandler = Callable[["PlatformLifecycleContext"], Any]


class PlatformLifecyclePhase(str, Enum):
    """Supported service lifecycle hook phases."""

    BEFORE_REGISTER = "before_register"
    AFTER_REGISTER = "after_register"
    BEFORE_START = "before_start"
    AFTER_START = "after_start"
    BEFORE_STOP = "before_stop"
    AFTER_STOP = "after_stop"
    ON_FAILURE = "on_failure"
    CUSTOM = "custom"


@dataclass(frozen=True)
class PlatformLifecycleContext:
    """Context passed to lifecycle handlers."""

    phase: PlatformLifecyclePhase
    service_name: str
    service: Any = None
    action: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    context_id: str = field(default_factory=lambda: f"platform-lifecycle-context-{uuid4().hex[:12]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if not self.service_name or not str(self.service_name).strip():
            raise ValueError("service_name is required")
        phase = self.phase if isinstance(self.phase, PlatformLifecyclePhase) else PlatformLifecyclePhase(str(self.phase))
        object.__setattr__(self, "phase", phase)
        object.__setattr__(self, "service_name", str(self.service_name))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))
        if self.action is not None:
            object.__setattr__(self, "action", str(self.action))
        if self.error is not None:
            object.__setattr__(self, "error", str(self.error))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "phase": self.phase.value,
            "service_name": self.service_name,
            "service_type": type(self.service).__name__ if self.service is not None else None,
            "action": self.action,
            "error": self.error,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class PlatformLifecycleHook:
    """Hook registration descriptor."""

    phase: PlatformLifecyclePhase
    handler: LifecycleHandler
    service_name: Optional[str] = None
    priority: int = 100
    hook_id: str = field(default_factory=lambda: f"platform-lifecycle-hook-{uuid4().hex[:12]}")
    metadata: Dict[str, Any] = field(default_factory=dict)
    active: bool = True

    def __post_init__(self) -> None:
        self.phase = self.phase if isinstance(self.phase, PlatformLifecyclePhase) else PlatformLifecyclePhase(str(self.phase))
        if not callable(self.handler):
            raise TypeError("lifecycle hook handler must be callable")
        if self.service_name is not None:
            self.service_name = str(self.service_name)
        self.priority = int(self.priority)
        self.metadata = dict(self.metadata or {})

    def matches(self, context: PlatformLifecycleContext) -> bool:
        return self.active and self.phase == context.phase and (self.service_name is None or self.service_name == context.service_name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hook_id": self.hook_id,
            "phase": self.phase.value,
            "service_name": self.service_name,
            "priority": self.priority,
            "active": self.active,
            "metadata": dict(self.metadata),
        }


@dataclass
class PlatformLifecycleExecution:
    """Execution record for one hook invocation."""

    hook_id: str
    phase: PlatformLifecyclePhase
    service_name: str
    ok: bool
    value: Any = None
    error: Optional[str] = None
    elapsed_ms: float = 0.0
    execution_id: str = field(default_factory=lambda: f"platform-lifecycle-execution-{uuid4().hex[:12]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        self.phase = self.phase if isinstance(self.phase, PlatformLifecyclePhase) else PlatformLifecyclePhase(str(self.phase))
        self.service_name = str(self.service_name)
        if self.error is not None:
            self.error = str(self.error)
        self.elapsed_ms = float(self.elapsed_ms)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "hook_id": self.hook_id,
            "phase": self.phase.value,
            "service_name": self.service_name,
            "ok": self.ok,
            "value": self.value,
            "error": self.error,
            "elapsed_ms": self.elapsed_ms,
            "created_at": self.created_at,
        }


class PlatformLifecycleHooks:
    """In-memory lifecycle hook registry and executor."""

    version = PLATFORM_LIFECYCLE_VERSION
    stage = PLATFORM_LIFECYCLE_STAGE

    def __init__(self, *, event_bus: Any = None, telemetry: Any = None, retain_history: bool = True, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.event_bus = event_bus
        self.telemetry = telemetry
        self.retain_history = bool(retain_history)
        self.metadata = dict(metadata or {})
        self._hooks: List[PlatformLifecycleHook] = []
        self._executions: List[PlatformLifecycleExecution] = []

    def register(
        self,
        phase: PlatformLifecyclePhase | str,
        handler: LifecycleHandler,
        *,
        service_name: Optional[str] = None,
        priority: int = 100,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PlatformLifecycleHook:
        hook = PlatformLifecycleHook(phase, handler, service_name=service_name, priority=priority, metadata=dict(metadata or {}))
        self._hooks.append(hook)
        self._hooks.sort(key=lambda item: (item.priority, item.hook_id))
        self._emit("platform.lifecycle.hook.registered", hook.to_dict())
        return hook

    def unregister(self, hook_id: str) -> bool:
        found = False
        for hook in self._hooks:
            if hook.hook_id == hook_id:
                hook.active = False
                found = True
        if found:
            self._emit("platform.lifecycle.hook.unregistered", {"hook_id": hook_id})
        return found

    def hooks(self, *, phase: Optional[PlatformLifecyclePhase | str] = None, service_name: Optional[str] = None, active_only: bool = False) -> List[PlatformLifecycleHook]:
        phase_value = None if phase is None else (phase if isinstance(phase, PlatformLifecyclePhase) else PlatformLifecyclePhase(str(phase)))
        result = list(self._hooks)
        if phase_value is not None:
            result = [hook for hook in result if hook.phase == phase_value]
        if service_name is not None:
            result = [hook for hook in result if hook.service_name in (None, str(service_name))]
        if active_only:
            result = [hook for hook in result if hook.active]
        return result

    def execute(
        self,
        phase: PlatformLifecyclePhase | str,
        service_name: str,
        *,
        service: Any = None,
        action: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        fail_fast: bool = False,
    ) -> List[PlatformLifecycleExecution]:
        context = PlatformLifecycleContext(phase, service_name, service=service, action=action, error=error, metadata=dict(metadata or {}))
        matched = [hook for hook in self._hooks if hook.matches(context)]
        executions: List[PlatformLifecycleExecution] = []
        self._emit("platform.lifecycle.phase.started", context.to_dict())
        for hook in matched:
            started_at = perf_counter()
            try:
                value = hook.handler(context)
                execution = PlatformLifecycleExecution(hook.hook_id, context.phase, context.service_name, True, value=value, elapsed_ms=round((perf_counter() - started_at) * 1000.0, 3))
            except Exception as exc:
                execution = PlatformLifecycleExecution(hook.hook_id, context.phase, context.service_name, False, error=str(exc), elapsed_ms=round((perf_counter() - started_at) * 1000.0, 3))
            executions.append(execution)
            if self.retain_history:
                self._executions.append(execution)
            self._record_telemetry(execution)
            self._emit("platform.lifecycle.hook.executed", execution.to_dict())
            if fail_fast and not execution.ok:
                break
        self._emit("platform.lifecycle.phase.completed", {"context": context.to_dict(), "executions": [item.to_dict() for item in executions]})
        return executions

    def executions(self, *, phase: Optional[PlatformLifecyclePhase | str] = None, service_name: Optional[str] = None, ok: Optional[bool] = None) -> List[PlatformLifecycleExecution]:
        phase_value = None if phase is None else (phase if isinstance(phase, PlatformLifecyclePhase) else PlatformLifecyclePhase(str(phase)))
        result = list(self._executions)
        if phase_value is not None:
            result = [item for item in result if item.phase == phase_value]
        if service_name is not None:
            result = [item for item in result if item.service_name == str(service_name)]
        if ok is not None:
            result = [item for item in result if item.ok is bool(ok)]
        return result

    def summary(self) -> Dict[str, Any]:
        active_hooks = [hook for hook in self._hooks if hook.active]
        return {
            "version": self.version,
            "stage": self.stage,
            "hook_count": len(self._hooks),
            "active_hook_count": len(active_hooks),
            "execution_count": len(self._executions),
            "failed_execution_count": sum(1 for execution in self._executions if not execution.ok),
            "phases": sorted({hook.phase.value for hook in self._hooks}),
        }

    def manifest(self) -> Dict[str, Any]:
        return {
            **self.summary(),
            "foundation_status": "frozen",
            "cli_status": "frozen",
            "sdk_status": "complete",
            "integration_status": "frozen",
            "workflow_status": "frozen",
            "additive_only": True,
            "hooks": [hook.to_dict() for hook in self._hooks],
            "metadata": dict(self.metadata),
        }

    def _emit(self, event_type: str, payload: Any) -> None:
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish(event_type, payload, source="platform.lifecycle", topic="lifecycle")

    def _record_telemetry(self, execution: PlatformLifecycleExecution) -> None:
        if self.telemetry is not None and hasattr(self.telemetry, "record"):
            self.telemetry.record(
                "lifecycle.hook.executed",
                source="platform.lifecycle",
                message=f"{execution.phase.value}:{execution.service_name}",
                metadata=execution.to_dict(),
            )


def create_lifecycle_hooks(**kwargs: Any) -> PlatformLifecycleHooks:
    return PlatformLifecycleHooks(**kwargs)
