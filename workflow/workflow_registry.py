"""Workflow registry for NTPE Stage-09.0."""
from __future__ import annotations
from typing import Dict, Iterable
from .workflow_models import WorkflowDefinition

class WorkflowRegistry:
    def __init__(self) -> None:
        self._items: Dict[str, WorkflowDefinition] = {}

    def register(self, workflow: WorkflowDefinition) -> WorkflowDefinition:
        self._items[workflow.name] = workflow
        return workflow

    def get(self, name: str) -> WorkflowDefinition:
        if name not in self._items:
            raise KeyError(f"workflow not registered: {name}")
        return self._items[name]

    def names(self) -> list[str]:
        return sorted(self._items.keys())

    def all(self) -> Iterable[WorkflowDefinition]:
        return tuple(self._items.values())

    def manifest(self) -> dict:
        return {"count": len(self._items), "workflows": self.names()}
