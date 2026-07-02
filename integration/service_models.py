"""Service Container models for NTPE Stage-08.6."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional
import time

SERVICE_CONTAINER_VERSION = "0.8.6"
SERVICE_CONTAINER_STAGE = "Stage-08.6 Service Container"

class ServiceLifetime(str, Enum):
    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"

@dataclass
class ServiceDescriptor:
    name: str
    factory: Callable[..., Any] | None = None
    instance: Any | None = None
    lifetime: ServiceLifetime | str = ServiceLifetime.TRANSIENT
    dependencies: list[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if isinstance(self.lifetime, str):
            self.lifetime = ServiceLifetime(self.lifetime)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "lifetime": self.lifetime.value,
            "dependencies": list(self.dependencies),
            "metadata": dict(self.metadata),
            "has_instance": self.instance is not None,
            "has_factory": self.factory is not None,
        }

@dataclass
class ServiceResolution:
    name: str
    value: Any = None
    ok: bool = True
    error: str = ""
    lifetime: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "error": self.error, "lifetime": self.lifetime, "value": self.value}
