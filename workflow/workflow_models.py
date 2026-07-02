"""Workflow models for NTPE 1.0 Beta Stage-09.0."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import time
import uuid

WORKFLOW_VERSION = "0.9.0"
WORKFLOW_STAGE = "NTPE 1.0 Beta Stage-09.0 Workflow Core"

class WorkflowStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class WorkflowStep:
    name: str
    action: Callable[..., Any] | None = None
    depends_on: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowDefinition:
    name: str
    steps: List[WorkflowStep] = field(default_factory=list)
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_step(self, name: str, action: Callable[..., Any] | None = None, *, depends_on: Optional[List[str]] = None, **metadata: Any) -> "WorkflowDefinition":
        self.steps.append(WorkflowStep(name=name, action=action, depends_on=list(depends_on or []), metadata=dict(metadata)))
        return self

@dataclass
class WorkflowExecutionResult:
    ok: bool
    workflow_id: str
    status: WorkflowStatus
    outputs: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "outputs": dict(self.outputs),
            "errors": list(self.errors),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }
