"""Runtime Resource model for NTPE 1.0 Beta Stage-11.6.

This module is additive. It models logical runtime resources without changing
frozen Foundation, CLI, SDK, Integration, Workflow, or Platform Services APIs.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

RUNTIME_RESOURCE_STAGE = "11.6"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class RuntimeResourceType(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    CACHE = "cache"
    MEMORY = "memory"
    CONFIG = "config"
    ARTIFACT = "artifact"
    LOG = "log"
    TEMP = "temp"
    CUSTOM = "custom"


class RuntimeResourceState(str, Enum):
    CREATED = "created"
    RESERVED = "reserved"
    ATTACHED = "attached"
    RELEASED = "released"
    DELETED = "deleted"
    ERROR = "error"


@dataclass(frozen=True)
class RuntimeResource:
    """Serializable runtime resource descriptor."""

    name: str
    resource_type: RuntimeResourceType | str = RuntimeResourceType.CUSTOM
    resource_id: str = field(default_factory=lambda: f"resource-{uuid4().hex[:12]}")
    uri: Optional[str] = None
    owner_id: Optional[str] = None
    session_id: Optional[str] = None
    job_id: Optional[str] = None
    pipeline_id: Optional[str] = None
    state: RuntimeResourceState | str = RuntimeResourceState.CREATED
    size: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    stage = RUNTIME_RESOURCE_STAGE

    def __post_init__(self) -> None:
        if not str(self.name).strip():
            raise ValueError("runtime resource name is required")
        object.__setattr__(self, "resource_type", RuntimeResourceType(self.resource_type))
        object.__setattr__(self, "state", RuntimeResourceState(self.state))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))
        if self.size is not None and int(self.size) < 0:
            raise ValueError("runtime resource size cannot be negative")
        if self.size is not None:
            object.__setattr__(self, "size", int(self.size))

    def transition(self, state: RuntimeResourceState | str, *, metadata: Optional[Dict[str, Any]] = None) -> "RuntimeResource":
        merged = dict(self.metadata)
        if metadata:
            merged.update(dict(metadata))
        return replace(self, state=RuntimeResourceState(state), metadata=merged, updated_at=utc_now_iso())

    def with_binding(
        self,
        *,
        session_id: Optional[str] = None,
        job_id: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> "RuntimeResource":
        return replace(
            self,
            session_id=session_id if session_id is not None else self.session_id,
            job_id=job_id if job_id is not None else self.job_id,
            pipeline_id=pipeline_id if pipeline_id is not None else self.pipeline_id,
            owner_id=owner_id if owner_id is not None else self.owner_id,
            updated_at=utc_now_iso(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "resource_id": self.resource_id,
            "name": self.name,
            "resource_type": self.resource_type.value,
            "uri": self.uri,
            "owner_id": self.owner_id,
            "session_id": self.session_id,
            "job_id": self.job_id,
            "pipeline_id": self.pipeline_id,
            "state": self.state.value,
            "size": self.size,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
