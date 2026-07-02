"""Runtime Pipeline API request helpers for NTPE 1.0 Beta Stage-11.4."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional, Tuple

from .runtime_errors import RuntimeApiValidationError
from .runtime_pipeline import RuntimePipelineStage

RUNTIME_PIPELINE_REQUEST_VERSION = "1.0.0-beta.11.4"
RUNTIME_PIPELINE_REQUEST_STAGE = "11.4"


@dataclass(frozen=True)
class RuntimePipelineCreateRequest:
    """Normalized create-pipeline payload."""

    name: Optional[str] = None
    stages: Tuple[RuntimePipelineStage, ...] = field(default_factory=tuple)
    provider: Optional[str] = None
    workflow_ref: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    version = RUNTIME_PIPELINE_REQUEST_VERSION
    stage = RUNTIME_PIPELINE_REQUEST_STAGE

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata or {}))
        normalized = []
        for index, stage in enumerate(self.stages or ()):  # type: ignore[assignment]
            if isinstance(stage, RuntimePipelineStage):
                normalized.append(stage)
            elif isinstance(stage, dict):
                payload = dict(stage)
                payload.setdefault("order", index)
                normalized.append(RuntimePipelineStage(**payload))
            else:
                normalized.append(RuntimePipelineStage(name=str(stage), order=index))
        object.__setattr__(self, "stages", tuple(normalized))
        for attr in ("name", "provider", "workflow_ref"):
            value = getattr(self, attr)
            if value is not None:
                object.__setattr__(self, attr, str(value))

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "RuntimePipelineCreateRequest":
        return cls(
            name=payload.get("name"),
            stages=tuple(payload.get("stages") or ()),
            provider=payload.get("provider"),
            workflow_ref=payload.get("workflow_ref"),
            metadata=payload.get("metadata") or {},
        )

    def to_payload(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "stages": self.stages,
            "provider": self.provider,
            "workflow_ref": self.workflow_ref,
            "metadata": dict(self.metadata),
        }
