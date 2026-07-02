"""Platform service health status models for NTPE 1.0 Beta Stage-10.3.

This module is additive. It does not change frozen Foundation, CLI, SDK,
Integration, or Workflow contracts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

PLATFORM_HEALTH_VERSION = "1.0.0-beta.10.3"
PLATFORM_HEALTH_STAGE = "10.3"


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp with second precision."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class PlatformHealthLevel(str, Enum):
    """Normalized health levels for platform services."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


_HEALTH_RANK = {
    PlatformHealthLevel.HEALTHY: 0,
    PlatformHealthLevel.UNKNOWN: 1,
    PlatformHealthLevel.WARNING: 2,
    PlatformHealthLevel.CRITICAL: 3,
}


def normalize_health_level(value: Any) -> PlatformHealthLevel:
    """Normalize bool/string/enum health values into PlatformHealthLevel."""
    if isinstance(value, PlatformHealthLevel):
        return value
    if isinstance(value, bool):
        return PlatformHealthLevel.HEALTHY if value else PlatformHealthLevel.CRITICAL
    if value is None:
        return PlatformHealthLevel.UNKNOWN
    return PlatformHealthLevel(str(value).lower())


def worst_health_level(levels: list[PlatformHealthLevel]) -> PlatformHealthLevel:
    """Return the most severe health level from a list."""
    if not levels:
        return PlatformHealthLevel.UNKNOWN
    return max(levels, key=lambda item: _HEALTH_RANK[item])


@dataclass(frozen=True)
class PlatformHealthCheckResult:
    """Single health-check result for one service."""

    service_name: str
    level: PlatformHealthLevel = PlatformHealthLevel.UNKNOWN
    ok: bool = False
    message: str = "not checked"
    response_time_ms: float = 0.0
    checked_at: str = field(default_factory=utc_now_iso)
    version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.service_name or not str(self.service_name).strip():
            raise ValueError("health check result requires service_name")
        object.__setattr__(self, "service_name", str(self.service_name))
        level = normalize_health_level(self.level)
        object.__setattr__(self, "level", level)
        object.__setattr__(self, "ok", bool(self.ok and level == PlatformHealthLevel.HEALTHY))
        object.__setattr__(self, "message", str(self.message))
        object.__setattr__(self, "response_time_ms", float(self.response_time_ms))
        object.__setattr__(self, "metadata", dict(self.metadata))
        if self.version is not None:
            object.__setattr__(self, "version", str(self.version))

    @classmethod
    def healthy(cls, service_name: str, message: str = "healthy", **metadata: Any) -> "PlatformHealthCheckResult":
        return cls(service_name=service_name, level=PlatformHealthLevel.HEALTHY, ok=True, message=message, metadata=dict(metadata))

    @classmethod
    def warning(cls, service_name: str, message: str = "warning", **metadata: Any) -> "PlatformHealthCheckResult":
        return cls(service_name=service_name, level=PlatformHealthLevel.WARNING, ok=False, message=message, metadata=dict(metadata))

    @classmethod
    def critical(cls, service_name: str, message: str = "critical", **metadata: Any) -> "PlatformHealthCheckResult":
        return cls(service_name=service_name, level=PlatformHealthLevel.CRITICAL, ok=False, message=message, metadata=dict(metadata))

    @classmethod
    def unknown(cls, service_name: str, message: str = "unknown", **metadata: Any) -> "PlatformHealthCheckResult":
        return cls(service_name=service_name, level=PlatformHealthLevel.UNKNOWN, ok=False, message=message, metadata=dict(metadata))

    def with_timing(self, response_time_ms: float) -> "PlatformHealthCheckResult":
        return PlatformHealthCheckResult(
            service_name=self.service_name,
            level=self.level,
            ok=self.ok,
            message=self.message,
            response_time_ms=response_time_ms,
            checked_at=self.checked_at,
            version=self.version,
            metadata=self.metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "level": self.level.value,
            "ok": self.ok,
            "message": self.message,
            "response_time_ms": self.response_time_ms,
            "checked_at": self.checked_at,
            "version": self.version,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class PlatformHealthSnapshot:
    """Immutable snapshot over latest known service health results."""

    results: tuple[PlatformHealthCheckResult, ...]
    generated_at: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    version = PLATFORM_HEALTH_VERSION
    stage = PLATFORM_HEALTH_STAGE

    @property
    def count(self) -> int:
        return len(self.results)

    @property
    def overall_level(self) -> PlatformHealthLevel:
        return worst_health_level([result.level for result in self.results])

    @property
    def ok(self) -> bool:
        return self.count > 0 and all(result.ok for result in self.results)

    def by_level(self, level: PlatformHealthLevel | str) -> list[PlatformHealthCheckResult]:
        resolved = normalize_health_level(level)
        return [result for result in self.results if result.level == resolved]

    def summary(self) -> Dict[str, Any]:
        healthy = self.by_level(PlatformHealthLevel.HEALTHY)
        warning = self.by_level(PlatformHealthLevel.WARNING)
        critical = self.by_level(PlatformHealthLevel.CRITICAL)
        unknown = self.by_level(PlatformHealthLevel.UNKNOWN)
        return {
            "version": self.version,
            "stage": self.stage,
            "ok": self.ok,
            "overall_level": self.overall_level.value,
            "count": self.count,
            "healthy": len(healthy),
            "warning": len(warning),
            "critical": len(critical),
            "unknown": len(unknown),
            "generated_at": self.generated_at,
        }

    def report(self) -> Dict[str, Any]:
        summary = self.summary()
        summary.update({
            "services": {result.service_name: result.to_dict() for result in self.results},
            "metadata": dict(self.metadata),
            "foundation_status": "frozen",
            "cli_status": "frozen",
            "sdk_status": "complete",
            "integration_status": "frozen",
            "workflow_status": "frozen",
            "additive_only": True,
        })
        return summary
