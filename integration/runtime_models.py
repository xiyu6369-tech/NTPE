"""Runtime integration models for NTPE Stage-08.1."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time
import uuid

RUNTIME_INTEGRATION_VERSION = "0.8.1"
RUNTIME_INTEGRATION_STAGE = "NTPE 1.0 Beta Stage-08.1 Runtime Integration"


@dataclass
class RuntimeMetadata:
    runtime_id: str
    name: str = "runtime"
    version: str = "1.0"
    status: str = "created"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, name: str = "runtime", version: str = "1.0", metadata: Optional[Dict[str, Any]] = None) -> "RuntimeMetadata":
        return cls(runtime_id=f"rt-{uuid.uuid4().hex[:12]}", name=name, version=version, metadata=dict(metadata or {}))

    def mark(self, status: str) -> None:
        self.status = status
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }


@dataclass
class RuntimeCommand:
    action: str
    payload: Dict[str, Any] = field(default_factory=dict)
    runtime_id: Optional[str] = None
    source: str = "integration"

    def to_dict(self) -> Dict[str, Any]:
        return {"action": self.action, "payload": dict(self.payload), "runtime_id": self.runtime_id, "source": self.source}


@dataclass
class RuntimeExecutionResult:
    ok: bool
    action: str
    runtime_id: Optional[str] = None
    value: Any = None
    error: Optional[str] = None
    status: str = "completed"

    @classmethod
    def success(cls, action: str, *, runtime_id: Optional[str] = None, value: Any = None, status: str = "completed") -> "RuntimeExecutionResult":
        return cls(True, action, runtime_id=runtime_id, value=value, status=status)

    @classmethod
    def failure(cls, action: str, error: str, *, runtime_id: Optional[str] = None, value: Any = None) -> "RuntimeExecutionResult":
        return cls(False, action, runtime_id=runtime_id, value=value, error=str(error), status="failed")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "action": self.action,
            "runtime_id": self.runtime_id,
            "value": self.value,
            "error": self.error,
            "status": self.status,
        }
