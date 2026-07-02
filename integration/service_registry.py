"""Service registry for NTPE Stage-08.6."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Optional

from .service_models import ServiceDescriptor, ServiceLifetime

class ServiceRegistry:
    def __init__(self) -> None:
        self._services: Dict[str, ServiceDescriptor] = {}

    def register(self, name: str, factory: Callable[..., Any] | None = None, *, instance: Any | None = None, lifetime: ServiceLifetime | str = ServiceLifetime.TRANSIENT, dependencies: Optional[Iterable[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> ServiceDescriptor:
        descriptor = ServiceDescriptor(name=name, factory=factory, instance=instance, lifetime=lifetime, dependencies=list(dependencies or []), metadata=dict(metadata or {}))
        self._services[name] = descriptor
        return descriptor

    def register_instance(self, name: str, instance: Any, *, metadata: Optional[Dict[str, Any]] = None) -> ServiceDescriptor:
        return self.register(name, instance=instance, lifetime=ServiceLifetime.SINGLETON, metadata=metadata)

    def unregister(self, name: str) -> bool:
        return self._services.pop(name, None) is not None

    def get(self, name: str) -> ServiceDescriptor | None:
        return self._services.get(name)

    def has(self, name: str) -> bool:
        return name in self._services

    def names(self) -> list[str]:
        return list(self._services.keys())

    def descriptors(self) -> list[ServiceDescriptor]:
        return list(self._services.values())

    def manifest(self) -> Dict[str, Any]:
        return {"count": len(self._services), "services": {name: desc.to_dict() for name, desc in self._services.items()}}
