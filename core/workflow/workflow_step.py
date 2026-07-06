# =====================================================
# NTPE 1.2 Professional
# Stage-17.1 Translation Workflow Engine
# =====================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .workflow_context import WorkflowContext
from .workflow_result import WorkflowStepResult

WorkflowCallable = Callable[[WorkflowContext], WorkflowStepResult]


@dataclass(frozen=True)
class WorkflowStep:
    name: str
    handler: WorkflowCallable
    required: bool = True
    description: str = ""

    def run(self, context: WorkflowContext) -> WorkflowStepResult:
        result = self.handler(context)
        if not isinstance(result, WorkflowStepResult):
            raise TypeError(f"workflow step {self.name} must return WorkflowStepResult")
        return result
