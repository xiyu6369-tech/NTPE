"""Scoped service cache for NTPE Stage-08.6."""
from __future__ import annotations

from typing import Any, Dict
import uuid

class ServiceScope:
    def __init__(self, scope_id: str | None = None) -> None:
        self.scope_id = scope_id or f"scope-{uuid.uuid4().hex[:8]}"
        self._instances: Dict[str, Any] = {}
        self.disposed = False

    def get(self, name: str) -> Any | None:
        return self._instances.get(name)

    def set(self, name: str, value: Any) -> Any:
        self._instances[name] = value
        return value

    def has(self, name: str) -> bool:
        return name in self._instances

    def dispose(self) -> None:
        self._instances.clear()
        self.disposed = True

    def manifest(self) -> dict:
        return {"scope_id": self.scope_id, "count": len(self._instances), "disposed": self.disposed}
