"""Platform service models for NTPE 1.0 Beta Stage-10.0."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

PLATFORM_SERVICES_VERSION = "1.0.0-beta.10.0"
PLATFORM_SERVICES_STAGE = "10.0"


class PlatformServiceStatus(str, Enum):
    REGISTERED = "registered"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass
class PlatformServiceDescriptor:
    name: str
    instance: Any = None
    version: str = PLATFORM_SERVICES_VERSION
    status: PlatformServiceStatus = PlatformServiceStatus.REGISTERED
    dependencies: list[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    service_id: str = field(default_factory=lambda: f"platform-service-{uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        if not self.name or not str(self.name).strip():
            raise ValueError("platform service name is required")
        self.name = str(self.name)
        self.dependencies = [str(item) for item in self.dependencies]
        self.metadata = dict(self.metadata)
        if not isinstance(self.status, PlatformServiceStatus):
            self.status = PlatformServiceStatus(str(self.status))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_id": self.service_id,
            "name": self.name,
            "version": self.version,
            "status": self.status.value,
            "dependencies": list(self.dependencies),
            "metadata": dict(self.metadata),
            "instance_type": type(self.instance).__name__ if self.instance is not None else None,
        }


@dataclass
class PlatformServiceResult:
    ok: bool
    action: str
    service: Optional[str] = None
    value: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, action: str, service: Optional[str] = None, *, value: Any = None, **metadata: Any) -> "PlatformServiceResult":
        return cls(True, action, service=service, value=value, metadata=dict(metadata))

    @classmethod
    def failure(cls, action: str, service: Optional[str], error: str, **metadata: Any) -> "PlatformServiceResult":
        return cls(False, action, service=service, error=str(error), metadata=dict(metadata))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "action": self.action,
            "service": self.service,
            "value": self.value,
            "error": self.error,
            "metadata": dict(self.metadata),
        }
