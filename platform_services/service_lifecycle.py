"""Service lifecycle helper for NTPE 1.0 Beta Stage-10.6."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .lifecycle_hooks import PlatformLifecycleHooks, PlatformLifecyclePhase


class PlatformServiceLifecycle:
    """Small adapter that applies lifecycle hooks around service objects."""

    version = "1.0.0-beta.10.6"
    stage = "10.6"

    def __init__(self, hooks: Optional[PlatformLifecycleHooks] = None, *, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.hooks = hooks or PlatformLifecycleHooks(metadata={"created_by": "service_lifecycle"})
        self.metadata = dict(metadata or {})

    def register_service(self, name: str, service: Any = None, *, registrar: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None) -> Any:
        self.hooks.execute(PlatformLifecyclePhase.BEFORE_REGISTER, name, service=service, action="register", metadata=metadata)
        value = registrar(name, service) if callable(registrar) else service
        self.hooks.execute(PlatformLifecyclePhase.AFTER_REGISTER, name, service=service, action="register", metadata=metadata)
        return value

    def start_service(self, name: str, service: Any = None, *, starter: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None) -> Any:
        self.hooks.execute(PlatformLifecyclePhase.BEFORE_START, name, service=service, action="start", metadata=metadata)
        try:
            value = starter(name, service) if callable(starter) else (service.start() if hasattr(service, "start") else {"started": True})
        except Exception as exc:
            self.hooks.execute(PlatformLifecyclePhase.ON_FAILURE, name, service=service, action="start", error=str(exc), metadata=metadata)
            raise
        self.hooks.execute(PlatformLifecyclePhase.AFTER_START, name, service=service, action="start", metadata=metadata)
        return value

    def stop_service(self, name: str, service: Any = None, *, stopper: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None) -> Any:
        self.hooks.execute(PlatformLifecyclePhase.BEFORE_STOP, name, service=service, action="stop", metadata=metadata)
        try:
            value = stopper(name, service) if callable(stopper) else (service.stop() if hasattr(service, "stop") else {"stopped": True})
        except Exception as exc:
            self.hooks.execute(PlatformLifecyclePhase.ON_FAILURE, name, service=service, action="stop", error=str(exc), metadata=metadata)
            raise
        self.hooks.execute(PlatformLifecyclePhase.AFTER_STOP, name, service=service, action="stop", metadata=metadata)
        return value

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "lifecycle_hooks": self.hooks.summary(),
            "additive_only": True,
            "metadata": dict(self.metadata),
        }


def create_service_lifecycle(hooks: Optional[PlatformLifecycleHooks] = None, **kwargs: Any) -> PlatformServiceLifecycle:
    return PlatformServiceLifecycle(hooks, **kwargs)
