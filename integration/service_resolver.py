"""Service resolver for NTPE Stage-08.6."""
from __future__ import annotations

from typing import Any, Dict, Optional, Set

from .service_factory import ServiceFactory
from .service_models import ServiceLifetime, ServiceResolution
from .service_registry import ServiceRegistry
from .service_scope import ServiceScope

class ServiceResolver:
    def __init__(self, registry: ServiceRegistry, *, factory: ServiceFactory | None = None) -> None:
        self.registry = registry
        self.factory = factory or ServiceFactory()
        self._singletons: Dict[str, Any] = {}
        self._resolving: Set[str] = set()

    def resolve(self, name: str, *, scope: Optional[ServiceScope] = None) -> Any:
        descriptor = self.registry.get(name)
        if descriptor is None:
            raise KeyError(f"Service not registered: {name}")
        if name in self._resolving:
            raise RuntimeError(f"Circular service dependency detected: {name}")
        if descriptor.lifetime == ServiceLifetime.SINGLETON and name in self._singletons:
            return self._singletons[name]
        if descriptor.lifetime == ServiceLifetime.SCOPED and scope is not None and scope.has(name):
            return scope.get(name)
        if descriptor.instance is not None and descriptor.lifetime == ServiceLifetime.SINGLETON:
            self._singletons[name] = descriptor.instance
            return descriptor.instance
        self._resolving.add(name)
        try:
            value = self.factory.create(descriptor, self)
        finally:
            self._resolving.discard(name)
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            self._singletons[name] = value
        elif descriptor.lifetime == ServiceLifetime.SCOPED and scope is not None:
            scope.set(name, value)
        return value

    def try_resolve(self, name: str, *, scope: Optional[ServiceScope] = None) -> ServiceResolution:
        try:
            descriptor = self.registry.get(name)
            value = self.resolve(name, scope=scope)
            return ServiceResolution(name=name, value=value, ok=True, lifetime=descriptor.lifetime.value if descriptor else "")
        except Exception as exc:
            return ServiceResolution(name=name, ok=False, error=str(exc))

    def clear_singletons(self) -> None:
        self._singletons.clear()
