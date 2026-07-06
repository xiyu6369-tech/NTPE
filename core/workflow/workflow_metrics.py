# =====================================================
# NTPE 1.2 Professional
# Stage-17.1 Translation Workflow Engine
# =====================================================

from __future__ import annotations

from typing import Any, Dict, Sequence

from .workflow_result import WorkflowStepResult


def build_workflow_metrics(steps: Sequence[WorkflowStepResult], artifacts: Dict[str, Any]) -> Dict[str, Any]:
    completed = [step for step in steps if step.status == "completed"]
    failed = [step for step in steps if step.status == "failed"]
    return {
        "step_count": len(steps),
        "completed_step_count": len(completed),
        "failed_step_count": len(failed),
        "artifact_count": len(artifacts),
        "has_translation": "translation" in artifacts,
        "has_quality_report": "quality_report" in artifacts,
        "has_export": "export" in artifacts,
    }
