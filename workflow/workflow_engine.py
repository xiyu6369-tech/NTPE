"""Workflow execution engine for NTPE Stage-09.0."""
from __future__ import annotations
from typing import Any, Dict
import time

from .workflow_context import WorkflowContext
from .workflow_models import WorkflowDefinition, WorkflowExecutionResult, WorkflowStatus

class WorkflowEngine:
    def __init__(self, *, event_bus: Any = None, service_container: Any = None) -> None:
        self.event_bus = event_bus
        self.service_container = service_container

    def _publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish(event_type, payload, topic="workflow", source="workflow_engine")

    def execute(self, workflow: WorkflowDefinition, context: WorkflowContext | None = None, **payload: Any) -> WorkflowExecutionResult:
        context = context or WorkflowContext(session_id=workflow.workflow_id)
        result = WorkflowExecutionResult(ok=False, workflow_id=workflow.workflow_id, status=WorkflowStatus.RUNNING)
        completed: set[str] = set()
        self._publish("workflow.started", {"workflow": workflow.name, "workflow_id": workflow.workflow_id})
        try:
            for step in workflow.steps:
                missing = [name for name in step.depends_on if name not in completed]
                if missing:
                    raise RuntimeError(f"step {step.name} missing dependencies: {missing}")
                self._publish("workflow.step.started", {"workflow": workflow.name, "step": step.name})
                if step.action is None:
                    output = {"step": step.name, "skipped": False}
                else:
                    output = step.action(context=context, payload=payload, services=self.service_container)
                result.outputs[step.name] = output
                context.set(step.name, output)
                completed.add(step.name)
                self._publish("workflow.step.completed", {"workflow": workflow.name, "step": step.name})
            result.ok = True
            result.status = WorkflowStatus.COMPLETED
            self._publish("workflow.completed", {"workflow": workflow.name, "workflow_id": workflow.workflow_id})
        except Exception as exc:  # noqa: BLE001 - stable workflow error isolation
            result.ok = False
            result.status = WorkflowStatus.FAILED
            result.errors.append(str(exc))
            self._publish("workflow.failed", {"workflow": workflow.name, "error": str(exc)})
        finally:
            result.completed_at = time.time()
        return result
