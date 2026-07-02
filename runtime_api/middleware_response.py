"""Runtime Middleware response models for NTPE 1.0 Beta Stage-11.7."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Tuple

from .runtime_middleware import RuntimeMiddleware


@dataclass(frozen=True)
class RuntimeMiddlewareListResponse:
    middlewares: Tuple[RuntimeMiddleware, ...] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_middlewares(cls, middlewares: Iterable[RuntimeMiddleware], *, metadata: Dict[str, Any] | None = None) -> "RuntimeMiddlewareListResponse":
        return cls(middlewares=tuple(middlewares), metadata=dict(metadata or {}))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "count": len(self.middlewares),
            "middlewares": [middleware.to_dict() for middleware in self.middlewares],
            "metadata": dict(self.metadata),
        }
