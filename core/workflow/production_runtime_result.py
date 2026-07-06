# =====================================================
# NTPE 1.2 Professional
# Stage-17.7 Production Runtime Integration
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ProductionRuntimeResult:
    runtime_id: str
    workflow_id: str
    status: str
    workflow_result: Any | None = None
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.status == "completed" and not self.errors

    def to_dict(self) -> Dict[str, Any]:
        workflow_payload = None
        if hasattr(self.workflow_result, "to_dict"):
            workflow_payload = self.workflow_result.to_dict()
        elif self.workflow_result is not None:
            workflow_payload = self.workflow_result
        return {
            "runtime_id": self.runtime_id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "success": self.success,
            "workflow_result": workflow_payload,
            "artifacts": dict(self.artifacts),
            "metrics": dict(self.metrics),
            "events": list(self.events),
            "errors": list(self.errors),
        }
