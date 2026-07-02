"""Pipeline models for NTPE 1.0 Beta Stage-09.2 Pipeline Orchestrator.

This module is additive and does not alter Stage-09.0/09.1 workflow contracts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import time
import uuid

PIPELINE_ORCHESTRATOR_VERSION = "0.9.2"
PIPELINE_ORCHESTRATOR_STAGE = "NTPE 1.0 Beta Stage-09.2 Pipeline Orchestrator"

class PipelineStatus(str, Enum):
    CREATED = "created"
    REGISTERED = "registered"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class PipelineStageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class PipelineStage:
    name: str
    action: Callable[..., Any] | None = None
    depends_on: List[str] = field(default_factory=list)
    job_name: str | None = None
    workflow_name: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: PipelineStageStatus = PipelineStageStatus.PENDING

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "depends_on": list(self.depends_on),
            "job_name": self.job_name,
            "workflow_name": self.workflow_name,
            "metadata": dict(self.metadata),
            "status": self.status.value,
        }

@dataclass
class PipelineDefinition:
    name: str
    stages: List[PipelineStage] = field(default_factory=list)
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: PipelineStatus = PipelineStatus.CREATED

    def add_stage(
        self,
        name: str,
        action: Callable[..., Any] | None = None,
        *,
        depends_on: Optional[List[str]] = None,
        job_name: str | None = None,
        workflow_name: str | None = None,
        **metadata: Any,
    ) -> "PipelineDefinition":
        self.stages.append(
            PipelineStage(
                name=name,
                action=action,
                depends_on=list(depends_on or []),
                job_name=job_name,
                workflow_name=workflow_name,
                metadata=dict(metadata),
            )
        )
        return self

    def stage_names(self) -> List[str]:
        return [stage.name for stage in self.stages]

@dataclass
class PipelineStageResult:
    name: str
    ok: bool
    status: PipelineStageStatus
    output: Any = None
    error: str | None = None
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "ok": self.ok,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

@dataclass
class PipelineExecutionResult:
    ok: bool
    pipeline_id: str
    status: PipelineStatus
    outputs: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    stage_results: Dict[str, PipelineStageResult] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "pipeline_id": self.pipeline_id,
            "status": self.status.value,
            "outputs": dict(self.outputs),
            "errors": list(self.errors),
            "stage_results": {name: result.to_dict() for name, result in self.stage_results.items()},
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }
