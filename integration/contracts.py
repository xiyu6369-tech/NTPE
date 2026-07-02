"""Stage-08.0 Integration Core contracts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time


@dataclass
class IntegrationComponent:
    name: str
    kind: str
    version: str = "1.0"
    instance: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "version": self.version,
            "has_instance": self.instance is not None,
            "metadata": dict(self.metadata),
        }


@dataclass
class IntegrationResult:
    ok: bool
    operation: str
    component: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    @classmethod
    def success(cls, operation: str, *, component: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> "IntegrationResult":
        return cls(True, operation, component=component, data=dict(data or {}))

    @classmethod
    def failure(cls, operation: str, error: str, *, component: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> "IntegrationResult":
        return cls(False, operation, component=component, data=dict(data or {}), errors=[str(error)])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "operation": self.operation,
            "component": self.component,
            "data": dict(self.data),
            "errors": list(self.errors),
            "created_at": self.created_at,
        }
