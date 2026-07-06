# =====================================================
# NTPE 1.2 Professional
# Stage-17.1 Translation Workflow Engine
# =====================================================

from __future__ import annotations

from .workflow_context import WorkflowContext
from .workflow_events import WORKFLOW_STEP_COMPLETED, WORKFLOW_STEP_STARTED, WorkflowEventBus
from .workflow_exceptions import WorkflowStepError
from .workflow_registry import WorkflowRegistry
from .workflow_result import WorkflowStepResult
from .workflow_state import WorkflowState


class WorkflowPipeline:
    def __init__(self, registry: WorkflowRegistry, event_bus: WorkflowEventBus | None = None) -> None:
        self.registry = registry
        self.event_bus = event_bus or WorkflowEventBus()

    def run(self, context: WorkflowContext, state: WorkflowState | None = None) -> list[WorkflowStepResult]:
        context.require_text()
        state = state or WorkflowState()
        results: list[WorkflowStepResult] = []
        for step in self.registry.all():
            state.start(step.name)
            self.event_bus.emit(WORKFLOW_STEP_STARTED, workflow_id=context.workflow_id, step=step.name)
            try:
                result = step.run(context)
                context.update_artifacts(result.output)
                context.record(step.name, status=result.status, message=result.message)
                results.append(result)
                state.complete(step.name)
                self.event_bus.emit(WORKFLOW_STEP_COMPLETED, workflow_id=context.workflow_id, step=step.name, status=result.status)
            except Exception as exc:
                state.fail(step.name)
                if step.required:
                    raise WorkflowStepError(f"workflow step failed: {step.name}: {exc}") from exc
                results.append(WorkflowStepResult(step_name=step.name, status="skipped", message=str(exc)))
        return results
