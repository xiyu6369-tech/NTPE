"""Runtime Session API models for NTPE 1.0 Beta Stage-11.2.

This module is additive. It does not modify frozen runtime, workflow,
platform services, CLI, SDK, or Stage-11.1 request/response contracts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

RUNTIME_SESSION_API_VERSION = "1.0.0-beta.11.2"
RUNTIME_SESSION_API_STAGE = "11.2"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class RuntimeSessionState(str, Enum):
    """Stable Runtime Session API states."""

    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class RuntimeSession:
    """Serializable session descriptor used by the Runtime Session API."""

    session_id: str = field(default_factory=lambda: f"runtime-session-{uuid4().hex[:12]}")
    state: RuntimeSessionState = RuntimeSessionState.CREATED
    name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    version = RUNTIME_SESSION_API_VERSION
    stage = RUNTIME_SESSION_API_STAGE

    def __post_init__(self) -> None:
        object.__setattr__(self, "session_id", str(self.session_id))
        object.__setattr__(self, "state", RuntimeSessionState(self.state))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))
        if self.name is not None:
            object.__setattr__(self, "name", str(self.name))

    def transition(self, state: RuntimeSessionState | str, *, metadata: Optional[Dict[str, Any]] = None) -> "RuntimeSession":
        merged_metadata = {**self.metadata, **dict(metadata or {})}
        return RuntimeSession(
            session_id=self.session_id,
            state=RuntimeSessionState(state),
            name=self.name,
            metadata=merged_metadata,
            created_at=self.created_at,
            updated_at=utc_now_iso(),
        )

    def with_metadata(self, **metadata: Any) -> "RuntimeSession":
        return self.transition(self.state, metadata=metadata)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "session_id": self.session_id,
            "state": self.state.value,
            "name": self.name,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
