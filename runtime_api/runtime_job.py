"""Runtime Job API models for NTPE 1.0 Beta Stage-11.3.

This module is additive and preserves Stage-11.1/11.2 public contracts.
It introduces a serializable job descriptor used by CLI, SDK, and future REST surfaces.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

RUNTIME_JOB_API_VERSION = "1.0.0-beta.11.3"
RUNTIME_JOB_API_STAGE = "11.3"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class RuntimeJobState(str, Enum):
    """Stable Runtime Job API states."""

    CREATED = "created"
    STARTED = "started"
    PAUSED = "paused"
    RESUMED = "resumed"
    STOPPED = "stopped"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class RuntimeJob:
    """Serializable job descriptor for runtime-level job orchestration."""

    job_id: str = field(default_factory=lambda: f"runtime-job-{uuid4().hex[:12]}")
    session_id: Optional[str] = None
    state: RuntimeJobState = RuntimeJobState.CREATED
    name: Optional[str] = None
    input_ref: Optional[str] = None
    output_ref: Optional[str] = None
    provider: Optional[str] = None
    pipeline: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    version = RUNTIME_JOB_API_VERSION
    stage = RUNTIME_JOB_API_STAGE

    def __post_init__(self) -> None:
        object.__setattr__(self, "job_id", str(self.job_id))
        if self.session_id is not None:
            object.__setattr__(self, "session_id", str(self.session_id))
        object.__setattr__(self, "state", RuntimeJobState(self.state))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))
        if self.result is not None:
            object.__setattr__(self, "result", dict(self.result or {}))
        for attr in ("name", "input_ref", "output_ref", "provider", "pipeline"):
            value = getattr(self, attr)
            if value is not None:
                object.__setattr__(self, attr, str(value))

    def transition(
        self,
        state: RuntimeJobState | str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> "RuntimeJob":
        merged_metadata = {**self.metadata, **dict(metadata or {})}
        final_result = dict(result) if result is not None else self.result
        return RuntimeJob(
            job_id=self.job_id,
            session_id=self.session_id,
            state=RuntimeJobState(state),
            name=self.name,
            input_ref=self.input_ref,
            output_ref=self.output_ref,
            provider=self.provider,
            pipeline=self.pipeline,
            metadata=merged_metadata,
            result=final_result,
            created_at=self.created_at,
            updated_at=utc_now_iso(),
        )

    def with_result(self, result: Dict[str, Any], *, metadata: Optional[Dict[str, Any]] = None) -> "RuntimeJob":
        return self.transition(RuntimeJobState.COMPLETED, metadata=metadata, result=result)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "job_id": self.job_id,
            "session_id": self.session_id,
            "state": self.state.value,
            "name": self.name,
            "input_ref": self.input_ref,
            "output_ref": self.output_ref,
            "provider": self.provider,
            "pipeline": self.pipeline,
            "metadata": dict(self.metadata),
            "result": dict(self.result) if self.result is not None else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
