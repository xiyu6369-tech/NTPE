# =====================================================
# NTPE 1.2 Professional
# Stage-17.1 Translation Workflow Engine
# =====================================================

from __future__ import annotations

from collections import OrderedDict
from typing import Iterable, List

from .workflow_step import WorkflowStep


class WorkflowRegistry:
    def __init__(self) -> None:
        self._steps: "OrderedDict[str, WorkflowStep]" = OrderedDict()

    def register(self, step: WorkflowStep) -> None:
        self._steps[step.name] = step

    def get(self, name: str) -> WorkflowStep | None:
        return self._steps.get(name)

    def all(self) -> List[WorkflowStep]:
        return list(self._steps.values())

    def names(self) -> List[str]:
        return list(self._steps.keys())

    def extend(self, steps: Iterable[WorkflowStep]) -> None:
        for step in steps:
            self.register(step)
