"""Platform service lifecycle manager for NTPE 1.0 Beta Stage-10.0."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .platform_events import PLATFORM_EVENTS
from .platform_models import PlatformServiceDescriptor, PlatformServiceResult, PlatformServiceStatus
from .service_registry import PlatformServiceRegistry


class PlatformServiceManager:
    version = "1.0.0-beta.10.0"
    stage = "10.0"

    def __init__(self, *, registry: Optional[PlatformServiceRegistry] = None, event_bus: Any = None, service_container: Any = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.registry = registry or PlatformServiceRegistry()
        self.event_bus = event_bus
        self.service_container = service_container
        self.metadata = dict(metadata or {})
        self.history: list[dict] = []

    def register_service(self, name: str, instance: Any = None, *, dependencies: Optional[list[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> PlatformServiceDescriptor:
        descriptor = self.registry.register(name, instance, dependencies=dependencies, metadata=metadata)
        if self.service_container is not None and hasattr(self.service_container, "register_instance") and instance is not None:
            self.service_container.register_instance(name, instance, metadata={"platform": True, **dict(metadata or {})})
        self._publish("registered", descriptor)
        return descriptor

    def start_service(self, name: str) -> PlatformServiceResult:
        descriptor = self.registry.require(name)
        try:
            self._ensure_dependencies(descriptor)
            descriptor.status = PlatformServiceStatus.STARTING
            if descriptor.instance is not None and hasattr(descriptor.instance, "start"):
                value = descriptor.instance.start()
            else:
                value = {"started": True}
            descriptor.status = PlatformServiceStatus.RUNNING
            self._publish("started", descriptor)
            return self._record(PlatformServiceResult.success("start", name, value=value))
        except Exception as exc:
            descriptor.status = PlatformServiceStatus.FAILED
            self._publish("failed", descriptor, error=str(exc))
            return self._record(PlatformServiceResult.failure("start", name, str(exc)))

    def stop_service(self, name: str) -> PlatformServiceResult:
        descriptor = self.registry.require(name)
        try:
            descriptor.status = PlatformServiceStatus.STOPPING
            if descriptor.instance is not None and hasattr(descriptor.instance, "stop"):
                value = descriptor.instance.stop()
            else:
                value = {"stopped": True}
            descriptor.status = PlatformServiceStatus.STOPPED
            self._publish("stopped", descriptor)
            return self._record(PlatformServiceResult.success("stop", name, value=value))
        except Exception as exc:
            descriptor.status = PlatformServiceStatus.FAILED
            self._publish("failed", descriptor, error=str(exc))
            return self._record(PlatformServiceResult.failure("stop", name, str(exc)))

    def start_all(self) -> list[PlatformServiceResult]:
        return [self.start_service(name) for name in self._dependency_order()]

    def stop_all(self) -> list[PlatformServiceResult]:
        return [self.stop_service(name) for name in reversed(self._dependency_order())]

    def health(self) -> Dict[str, Any]:
        services = {service.name: service.status.value for service in self.registry.services()}
        ok = all(status in {PlatformServiceStatus.RUNNING.value, PlatformServiceStatus.STOPPED.value, PlatformServiceStatus.REGISTERED.value} for status in services.values())
        payload = {"ok": ok, "services": services, "count": len(services)}
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish(PLATFORM_EVENTS["health"], payload, source="platform", topic="services")
        return payload

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
            "registry": self.registry.manifest(),
            "history": list(self.history),
            "bridges": {
                "event_bus_attached": self.event_bus is not None,
                "service_container_attached": self.service_container is not None,
            },
            "metadata": dict(self.metadata),
        }

    def _ensure_dependencies(self, descriptor: PlatformServiceDescriptor) -> None:
        for dependency in descriptor.dependencies:
            dep = self.registry.require(dependency)
            if dep.status not in {PlatformServiceStatus.RUNNING, PlatformServiceStatus.REGISTERED, PlatformServiceStatus.STOPPED}:
                raise RuntimeError(f"platform service dependency unavailable: {dependency}")

    def _dependency_order(self) -> list[str]:
        ordered: list[str] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(name: str) -> None:
            if name in visited:
                return
            if name in visiting:
                raise RuntimeError(f"platform service dependency cycle: {name}")
            visiting.add(name)
            descriptor = self.registry.require(name)
            for dependency in descriptor.dependencies:
                visit(dependency)
            visiting.remove(name)
            visited.add(name)
            ordered.append(name)

        for service_name in self.registry.names():
            visit(service_name)
        return ordered

    def _publish(self, key: str, descriptor: PlatformServiceDescriptor, **extra: Any) -> None:
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            payload = descriptor.to_dict()
            payload.update(extra)
            self.event_bus.publish(PLATFORM_EVENTS[key], payload, source="platform", topic="services")

    def _record(self, result: PlatformServiceResult) -> PlatformServiceResult:
        self.history.append(result.to_dict())
        return result
