from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .contracts import ProviderRequest


@dataclass
class ExecutionContext:
    """Runtime-scoped execution context for provider calls.

    The object is intentionally small and serialisable so Translation Runtime,
    CLI, Web UI, and plugin layers can pass execution metadata without importing
    any concrete provider implementation.
    """

    request: ProviderRequest
    provider_name: Optional[str] = None
    model: Optional[str] = None
    session_id: Optional[str] = None
    runtime_id: Optional[str] = None
    priority: int = 0
    stream: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    cancelled: bool = False

    def cancel(self) -> None:
        self.cancelled = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "model": self.model or self.request.model,
            "session_id": self.session_id,
            "runtime_id": self.runtime_id,
            "priority": self.priority,
            "stream": self.stream or self.request.stream,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "cancelled": self.cancelled,
        }
