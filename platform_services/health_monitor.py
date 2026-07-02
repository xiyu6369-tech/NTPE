"""Service health monitor for NTPE 1.0 Beta Stage-10.3.

The monitor is an additive platform-services layer. It can evaluate services from
PlatformServiceRegistry and from explicitly registered checks without changing
frozen Foundation, CLI, SDK, Integration, or Workflow behavior.
"""
from __future__ import annotations

from time import perf_counter
from typing import Any, Callable, Dict, Iterable, Optional

from .platform_models import PlatformServiceDescriptor, PlatformServiceStatus
from .service_registry import PlatformServiceRegistry
from .health_status import (
    PLATFORM_HEALTH_STAGE,
    PLATFORM_HEALTH_VERSION,
    PlatformHealthCheckResult,
    PlatformHealthLevel,
    PlatformHealthSnapshot,
    normalize_health_level,
)

HealthCheckCallable = Callable[[PlatformServiceDescriptor], Any]


class PlatformServiceHealthMonitor:
    """Evaluate and cache platform-service health status."""

    version = PLATFORM_HEALTH_VERSION
    stage = PLATFORM_HEALTH_STAGE

    def __init__(self, registry: Optional[PlatformServiceRegistry] = None, *, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.registry = registry or PlatformServiceRegistry()
        self.metadata = dict(metadata or {})
        self._checks: Dict[str, HealthCheckCallable] = {}
        self._latest: Dict[str, PlatformHealthCheckResult] = {}

    def register_check(self, service_name: str, check: HealthCheckCallable) -> "PlatformServiceHealthMonitor":
        if not service_name or not str(service_name).strip():
            raise ValueError("health check requires service_name")
        if not callable(check):
            raise TypeError("health check must be callable")
        self._checks[str(service_name)] = check
        return self

    def unregister_check(self, service_name: str) -> "PlatformServiceHealthMonitor":
        self._checks.pop(str(service_name), None)
        return self

    def check_service(self, service_name: str) -> PlatformHealthCheckResult:
        descriptor = self.registry.get(str(service_name))
        if descriptor is None:
            result = PlatformHealthCheckResult.unknown(str(service_name), "service not registered")
            self._latest[str(service_name)] = result
            return result
        result = self._run_check(descriptor)
        self._latest[descriptor.name] = result
        return result

    def check_all(self, services: Optional[Iterable[str]] = None) -> PlatformHealthSnapshot:
        names = list(services) if services is not None else self.registry.names()
        results = tuple(self.check_service(name) for name in names)
        return PlatformHealthSnapshot(results, metadata={"source": "check_all", **self.metadata})

    def snapshot(self) -> PlatformHealthSnapshot:
        return PlatformHealthSnapshot(tuple(self._latest.values()), metadata={"source": "latest", **self.metadata})

    def summary(self) -> Dict[str, Any]:
        return self.snapshot().summary()

    def report(self) -> Dict[str, Any]:
        return self.snapshot().report()

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "registered_checks": sorted(self._checks.keys()),
            "latest_count": len(self._latest),
            "registry_count": self.registry.manifest()["count"],
            "foundation_status": "frozen",
            "cli_status": "frozen",
            "sdk_status": "complete",
            "integration_status": "frozen",
            "workflow_status": "frozen",
            "additive_only": True,
            "metadata": dict(self.metadata),
        }

    def _run_check(self, descriptor: PlatformServiceDescriptor) -> PlatformHealthCheckResult:
        started_at = perf_counter()
        try:
            raw = self._invoke_check(descriptor)
            result = self._coerce_result(descriptor, raw)
        except Exception as exc:
            result = PlatformHealthCheckResult.critical(descriptor.name, f"health check failed: {exc}")
        elapsed = (perf_counter() - started_at) * 1000.0
        return result.with_timing(round(elapsed, 3))

    def _invoke_check(self, descriptor: PlatformServiceDescriptor) -> Any:
        if descriptor.name in self._checks:
            return self._checks[descriptor.name](descriptor)
        instance = descriptor.instance
        if instance is not None and hasattr(instance, "health") and callable(instance.health):
            return instance.health()
        if instance is not None and hasattr(instance, "health_check") and callable(instance.health_check):
            return instance.health_check()
        return self._default_check(descriptor)

    def _default_check(self, descriptor: PlatformServiceDescriptor) -> PlatformHealthCheckResult:
        if descriptor.status == PlatformServiceStatus.FAILED:
            return PlatformHealthCheckResult.critical(descriptor.name, "service status is failed", status=descriptor.status.value)
        if descriptor.status in {PlatformServiceStatus.STARTING, PlatformServiceStatus.STOPPING}:
            return PlatformHealthCheckResult.warning(descriptor.name, f"service status is {descriptor.status.value}", status=descriptor.status.value)
        if descriptor.status in {PlatformServiceStatus.REGISTERED, PlatformServiceStatus.RUNNING, PlatformServiceStatus.STOPPED}:
            return PlatformHealthCheckResult.healthy(descriptor.name, f"service status is {descriptor.status.value}", status=descriptor.status.value)
        return PlatformHealthCheckResult.unknown(descriptor.name, "service status is unknown", status=str(descriptor.status))

    def _coerce_result(self, descriptor: PlatformServiceDescriptor, raw: Any) -> PlatformHealthCheckResult:
        if isinstance(raw, PlatformHealthCheckResult):
            return raw
        if isinstance(raw, bool):
            return PlatformHealthCheckResult(
                service_name=descriptor.name,
                level=PlatformHealthLevel.HEALTHY if raw else PlatformHealthLevel.CRITICAL,
                ok=raw,
                message="healthy" if raw else "unhealthy",
                version=descriptor.version,
            )
        if isinstance(raw, str):
            level = normalize_health_level(raw)
            return PlatformHealthCheckResult(
                service_name=descriptor.name,
                level=level,
                ok=level == PlatformHealthLevel.HEALTHY,
                message=raw,
                version=descriptor.version,
            )
        if isinstance(raw, dict):
            level = normalize_health_level(raw.get("level", raw.get("status", PlatformHealthLevel.UNKNOWN.value)))
            ok = bool(raw.get("ok", level == PlatformHealthLevel.HEALTHY))
            return PlatformHealthCheckResult(
                service_name=str(raw.get("service_name", descriptor.name)),
                level=level,
                ok=ok,
                message=str(raw.get("message", level.value)),
                version=str(raw.get("version", descriptor.version)) if raw.get("version", descriptor.version) is not None else None,
                metadata=dict(raw.get("metadata", {})),
            )
        return PlatformHealthCheckResult.unknown(descriptor.name, "unsupported health check result", result_type=type(raw).__name__)


def create_health_monitor(registry: Optional[PlatformServiceRegistry] = None, **kwargs: Any) -> PlatformServiceHealthMonitor:
    return PlatformServiceHealthMonitor(registry, **kwargs)
