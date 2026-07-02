"""Runtime Pipeline model for NTPE 1.0 Beta Stage-11.4.

This module is additive and does not modify frozen Workflow or Platform
Services. It provides a stable API-side pipeline descriptor for CLI, SDK, and
future REST/Web surfaces.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, Optional, Tuple
from uuid import uuid4

from .runtime_errors import RuntimeApiValidationError

RUNTIME_PIPELINE_VERSION = "1.0.0-beta.11.4"
RUNTIME_PIPELINE_STAGE = "11.4"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class RuntimePipelineState(str, Enum):
    CREATED = "created"
    VALIDATED = "validated"
    STARTED = "started"
    PAUSED = "paused"
    RESUMED = "resumed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class RuntimePipelineStage:
    """Serializable API-side pipeline stage descriptor."""

    name: str
    component: Optional[str] = None
    order: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    version = RUNTIME_PIPELINE_VERSION
    stage = RUNTIME_PIPELINE_STAGE

    def __post_init__(self) -> None:
        if not str(self.name or "").strip():
            raise RuntimeApiValidationError("pipeline stage name is required")
        object.__setattr__(self, "name", str(self.name))
        if self.component is not None:
            object.__setattr__(self, "component", str(self.component))
        object.__setattr__(self, "order", int(self.order))
        object.__setattr__(self, "enabled", bool(self.enabled))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "name": self.name,
            "component": self.component,
            "order": self.order,
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RuntimePipeline:
    """API-side pipeline aggregate independent from internal workflow objects."""

    pipeline_id: str = field(default_factory=lambda: f"runtime-pipeline-{uuid4().hex[:12]}")
    name: Optional[str] = None
    state: RuntimePipelineState | str = RuntimePipelineState.CREATED
    stages: Tuple[RuntimePipelineStage, ...] = field(default_factory=tuple)
    provider: Optional[str] = None
    workflow_ref: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    version = RUNTIME_PIPELINE_VERSION
    stage = RUNTIME_PIPELINE_STAGE

    def __post_init__(self) -> None:
        object.__setattr__(self, "pipeline_id", str(self.pipeline_id))
        object.__setattr__(self, "state", RuntimePipelineState(self.state))
        normalized_stages = []
        for index, stage in enumerate(self.stages or ()):  # type: ignore[assignment]
            if isinstance(stage, RuntimePipelineStage):
                normalized_stages.append(stage)
            elif isinstance(stage, dict):
                payload = dict(stage)
                payload.setdefault("order", index)
                normalized_stages.append(RuntimePipelineStage(**payload))
            else:
                normalized_stages.append(RuntimePipelineStage(name=str(stage), order=index))
        object.__setattr__(self, "stages", tuple(normalized_stages))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))
        if self.result is not None:
            object.__setattr__(self, "result", dict(self.result or {}))
        for attr in ("name", "provider", "workflow_ref"):
            value = getattr(self, attr)
            if value is not None:
                object.__setattr__(self, attr, str(value))

    def transition(
        self,
        state: RuntimePipelineState | str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> "RuntimePipeline":
        return RuntimePipeline(
            pipeline_id=self.pipeline_id,
            name=self.name,
            state=RuntimePipelineState(state),
            stages=self.stages,
            provider=self.provider,
            workflow_ref=self.workflow_ref,
            metadata={**self.metadata, **dict(metadata or {})},
            result=dict(result) if result is not None else self.result,
            created_at=self.created_at,
            updated_at=utc_now_iso(),
        )

    def with_stage(self, stage: RuntimePipelineStage) -> "RuntimePipeline":
        stages = tuple(sorted((*self.stages, stage), key=lambda item: item.order))
        return RuntimePipeline(
            pipeline_id=self.pipeline_id,
            name=self.name,
            state=self.state,
            stages=stages,
            provider=self.provider,
            workflow_ref=self.workflow_ref,
            metadata=self.metadata,
            result=self.result,
            created_at=self.created_at,
            updated_at=utc_now_iso(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "state": self.state.value,
            "stages": [stage.to_dict() for stage in self.stages],
            "stage_count": len(self.stages),
            "provider": self.provider,
            "workflow_ref": self.workflow_ref,
            "metadata": dict(self.metadata),
            "result": dict(self.result) if self.result is not None else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
