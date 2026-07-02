"""Service discovery layer for NTPE 1.0 Beta Stage-10.2.

This module is additive to Stage-10.0/10.1. It provides deterministic in-memory
lookup and filtering over platform service descriptors without changing frozen
Foundation, CLI, SDK, Integration, or Workflow contracts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional

from .platform_models import PlatformServiceDescriptor, PlatformServiceStatus
from .service_registry import PlatformServiceRegistry

PLATFORM_DISCOVERY_VERSION = "1.0.0-beta.10.2"
PLATFORM_DISCOVERY_STAGE = "10.2"


@dataclass(frozen=True)
class ServiceDiscoveryQuery:
    """Immutable query object for platform service discovery."""

    name: Optional[str] = None
    status: Optional[str] = None
    tag: Optional[str] = None
    dependency: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))
        if self.name is not None:
            object.__setattr__(self, "name", str(self.name))
        if self.status is not None:
            object.__setattr__(self, "status", PlatformServiceStatus(str(self.status)).value)
        if self.tag is not None:
            object.__setattr__(self, "tag", str(self.tag))
        if self.dependency is not None:
            object.__setattr__(self, "dependency", str(self.dependency))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "tag": self.tag,
            "dependency": self.dependency,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ServiceDiscoveryResult:
    """Resolved discovery result snapshot."""

    query: ServiceDiscoveryQuery
    services: tuple[PlatformServiceDescriptor, ...]

    @property
    def count(self) -> int:
        return len(self.services)

    def names(self) -> list[str]:
        return [service.name for service in self.services]

    def first(self) -> Optional[PlatformServiceDescriptor]:
        return self.services[0] if self.services else None

    def require_one(self) -> PlatformServiceDescriptor:
        if not self.services:
            raise KeyError("no platform service matched discovery query")
        if len(self.services) > 1:
            raise ValueError("multiple platform services matched discovery query")
        return self.services[0]

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": PLATFORM_DISCOVERY_VERSION,
            "stage": PLATFORM_DISCOVERY_STAGE,
            "count": self.count,
            "query": self.query.to_dict(),
            "services": [service.to_dict() for service in self.services],
        }


class PlatformServiceDiscovery:
    """Read-only service discovery facade over PlatformServiceRegistry."""

    version = PLATFORM_DISCOVERY_VERSION
    stage = PLATFORM_DISCOVERY_STAGE

    def __init__(self, registry: PlatformServiceRegistry, *, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.registry = registry
        self.metadata = dict(metadata or {})

    def discover(self, query: Optional[ServiceDiscoveryQuery] = None, **filters: Any) -> ServiceDiscoveryResult:
        resolved_query = query or ServiceDiscoveryQuery(**filters)
        services = tuple(service for service in self.registry.services() if self._matches(service, resolved_query))
        return ServiceDiscoveryResult(resolved_query, services)

    def by_name(self, name: str) -> Optional[PlatformServiceDescriptor]:
        return self.discover(name=name).first()

    def require(self, name: str) -> PlatformServiceDescriptor:
        service = self.by_name(name)
        if service is None:
            raise KeyError(f"platform service not discovered: {name}")
        return service

    def running(self) -> ServiceDiscoveryResult:
        return self.discover(status=PlatformServiceStatus.RUNNING.value)

    def by_tag(self, tag: str) -> ServiceDiscoveryResult:
        return self.discover(tag=tag)

    def depending_on(self, dependency: str) -> ServiceDiscoveryResult:
        return self.discover(dependency=dependency)

    def metadata_match(self, **metadata: Any) -> ServiceDiscoveryResult:
        return self.discover(metadata=metadata)

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "foundation_status": "frozen",
            "cli_status": "frozen",
            "sdk_status": "complete",
            "integration_status": "frozen",
            "workflow_status": "frozen",
            "additive_only": True,
            "registry_count": self.registry.manifest()["count"],
            "metadata": dict(self.metadata),
        }

    def _matches(self, service: PlatformServiceDescriptor, query: ServiceDiscoveryQuery) -> bool:
        if query.name is not None and service.name != query.name:
            return False
        if query.status is not None and service.status.value != query.status:
            return False
        if query.tag is not None:
            tags = service.metadata.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]
            if query.tag not in {str(tag) for tag in tags}:
                return False
        if query.dependency is not None and query.dependency not in service.dependencies:
            return False
        for key, value in query.metadata.items():
            if service.metadata.get(key) != value:
                return False
        return True


def create_service_discovery(registry: PlatformServiceRegistry, **kwargs: Any) -> PlatformServiceDiscovery:
    return PlatformServiceDiscovery(registry, **kwargs)
