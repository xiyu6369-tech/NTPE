"""Platform service registry for NTPE 1.0 Beta Stage-10.0."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from .platform_models import PlatformServiceDescriptor


class PlatformServiceRegistry:
    version = "1.0.0-beta.10.0"
    stage = "10.0"

    def __init__(self) -> None:
        self._services: Dict[str, PlatformServiceDescriptor] = {}

    def register(self, name: str, instance: Any = None, *, version: Optional[str] = None, dependencies: Optional[Iterable[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> PlatformServiceDescriptor:
        descriptor = PlatformServiceDescriptor(
            name=name,
            instance=instance,
            version=version or self.version,
            dependencies=list(dependencies or []),
            metadata=dict(metadata or {}),
        )
        self._services[descriptor.name] = descriptor
        return descriptor

    def get(self, name: str) -> Optional[PlatformServiceDescriptor]:
        return self._services.get(name)

    def require(self, name: str) -> PlatformServiceDescriptor:
        descriptor = self.get(name)
        if descriptor is None:
            raise KeyError(f"platform service not registered: {name}")
        return descriptor

    def names(self) -> list[str]:
        return list(self._services.keys())

    def services(self) -> tuple[PlatformServiceDescriptor, ...]:
        return tuple(self._services.values())

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "count": len(self._services),
            "services": [service.to_dict() for service in self.services()],
        }
