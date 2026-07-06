# =====================================================
# NTPE 1.2 Professional
# Stage-17.1 Translation Workflow Engine
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class WorkflowStepResult:
    step_name: str
    status: str = "completed"
    output: Dict[str, Any] = field(default_factory=dict)
    message: str = ""


@dataclass
class WorkflowResult:
    workflow_id: str
    status: str
    steps: List[WorkflowStepResult] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.status == "completed" and not self.errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "status": self.status,
            "success": self.success,
            "steps": [step.__dict__ for step in self.steps],
            "artifacts": dict(self.artifacts),
            "metrics": dict(self.metrics),
            "errors": list(self.errors),
        }
