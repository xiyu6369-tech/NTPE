"""Runtime Job API request helpers for NTPE 1.0 Beta Stage-11.3."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .runtime_errors import RuntimeApiValidationError

RUNTIME_JOB_REQUEST_VERSION = "1.0.0-beta.11.3"
RUNTIME_JOB_REQUEST_STAGE = "11.3"


@dataclass(frozen=True)
class RuntimeJobCreateRequest:
    """Normalized create-job payload."""

    session_id: Optional[str] = None
    name: Optional[str] = None
    input_ref: Optional[str] = None
    output_ref: Optional[str] = None
    provider: Optional[str] = None
    pipeline: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    version = RUNTIME_JOB_REQUEST_VERSION
    stage = RUNTIME_JOB_REQUEST_STAGE

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata or {}))
        if self.input_ref is not None and not str(self.input_ref).strip():
            raise RuntimeApiValidationError("job input_ref cannot be blank")
        if self.session_id is not None:
            object.__setattr__(self, "session_id", str(self.session_id))

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "RuntimeJobCreateRequest":
        return cls(
            session_id=payload.get("session_id"),
            name=payload.get("name"),
            input_ref=payload.get("input_ref"),
            output_ref=payload.get("output_ref"),
            provider=payload.get("provider"),
            pipeline=payload.get("pipeline"),
            metadata=payload.get("metadata") or {},
        )

    def to_payload(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "name": self.name,
            "input_ref": self.input_ref,
            "output_ref": self.output_ref,
            "provider": self.provider,
            "pipeline": self.pipeline,
            "metadata": dict(self.metadata),
        }
