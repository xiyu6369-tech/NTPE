"""Runtime Resource request models for NTPE Stage-11.6."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .runtime_resource import RuntimeResourceState, RuntimeResourceType


@dataclass(frozen=True)
class RuntimeResourceCreateRequest:
    name: str
    resource_type: RuntimeResourceType | str = RuntimeResourceType.CUSTOM
    uri: Optional[str] = None
    owner_id: Optional[str] = None
    session_id: Optional[str] = None
    job_id: Optional[str] = None
    pipeline_id: Optional[str] = None
    size: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.name).strip():
            raise ValueError("runtime resource name is required")
        object.__setattr__(self, "resource_type", RuntimeResourceType(self.resource_type))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "RuntimeResourceCreateRequest":
        return cls(
            name=str(payload.get("name") or ""),
            resource_type=payload.get("resource_type") or RuntimeResourceType.CUSTOM,
            uri=payload.get("uri"),
            owner_id=payload.get("owner_id"),
            session_id=payload.get("session_id"),
            job_id=payload.get("job_id"),
            pipeline_id=payload.get("pipeline_id"),
            size=payload.get("size"),
            metadata=dict(payload.get("metadata") or {}),
        )

    def to_payload(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "resource_type": self.resource_type.value,
            "uri": self.uri,
            "owner_id": self.owner_id,
            "session_id": self.session_id,
            "job_id": self.job_id,
            "pipeline_id": self.pipeline_id,
            "size": self.size,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RuntimeResourceTransitionRequest:
    resource_id: str
    state: RuntimeResourceState | str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.resource_id).strip():
            raise ValueError("resource_id is required")
        object.__setattr__(self, "state", RuntimeResourceState(self.state))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))
