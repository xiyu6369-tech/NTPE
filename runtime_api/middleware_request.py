"""Runtime Middleware request models for NTPE 1.0 Beta Stage-11.7."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from .runtime_errors import RuntimeApiValidationError
from .runtime_middleware import RuntimeMiddlewareState


@dataclass(frozen=True)
class RuntimeMiddlewareRegisterRequest:
    name: str
    priority: int = 100
    state: RuntimeMiddlewareState | str = RuntimeMiddlewareState.ENABLED
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name or not str(self.name).strip():
            raise RuntimeApiValidationError("middleware name is required")
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "priority", int(self.priority))
        object.__setattr__(self, "state", RuntimeMiddlewareState(self.state))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "RuntimeMiddlewareRegisterRequest":
        return cls(
            name=payload.get("name", ""),
            priority=payload.get("priority", 100),
            state=payload.get("state", RuntimeMiddlewareState.ENABLED),
            metadata=payload.get("metadata") or {},
        )

    def to_payload(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "priority": self.priority,
            "state": self.state.value,
            "metadata": dict(self.metadata),
        }
