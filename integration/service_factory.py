"""Factory helper for NTPE Stage-08.6 Service Container."""
from __future__ import annotations

from typing import Any

from .service_models import ServiceDescriptor

class ServiceFactory:
    def create(self, descriptor: ServiceDescriptor, resolver: Any) -> Any:
        if descriptor.instance is not None:
            return descriptor.instance
        if descriptor.factory is None:
            raise ValueError(f"Service '{descriptor.name}' has no factory or instance")
        dependencies = {name: resolver.resolve(name) for name in descriptor.dependencies}
        try:
            return descriptor.factory(**dependencies)
        except TypeError:
            # Backward-compatible fallback for simple zero-arg factories.
            if dependencies:
                raise
            return descriptor.factory()
