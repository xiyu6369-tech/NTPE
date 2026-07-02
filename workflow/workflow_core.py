"""Workflow Core for NTPE 1.0 Beta Stage-09.0.

This layer is additive and depends on frozen Integration v1.0 surfaces only.
"""
from __future__ import annotations
from typing import Any, Callable, Optional

from .workflow_context import WorkflowContext
from .workflow_engine import WorkflowEngine
from .workflow_models import WORKFLOW_STAGE, WORKFLOW_VERSION, WorkflowDefinition
from .workflow_registry import WorkflowRegistry

class WorkflowCore:
    version = WORKFLOW_VERSION
    stage = WORKFLOW_STAGE

    def __init__(self, *, event_bus: Any = None, service_container: Any = None, metadata: Optional[dict] = None) -> None:
        self.registry = WorkflowRegistry()
        self.engine = WorkflowEngine(event_bus=event_bus, service_container=service_container)
        self.event_bus = event_bus
        self.service_container = service_container
        self.metadata = dict(metadata or {})

    def create_workflow(self, name: str, **metadata: Any) -> WorkflowDefinition:
        workflow = WorkflowDefinition(name=name, metadata=dict(metadata))
        self.registry.register(workflow)
        return workflow

    def register_workflow(self, workflow: WorkflowDefinition) -> WorkflowDefinition:
        return self.registry.register(workflow)

    def add_step(self, workflow_name: str, step_name: str, action: Callable[..., Any] | None = None, *, depends_on: Optional[list[str]] = None, **metadata: Any) -> WorkflowDefinition:
        workflow = self.registry.get(workflow_name)
        return workflow.add_step(step_name, action, depends_on=depends_on, **metadata)

    def execute(self, workflow_name: str, *, context: WorkflowContext | None = None, **payload: Any):
        return self.engine.execute(self.registry.get(workflow_name), context=context, **payload)

    def manifest(self) -> dict:
        return {
            "version": self.version,
            "stage": self.stage,
            "foundation_status": "frozen",
            "integration_status": "frozen",
            "additive_only": True,
            "registry": self.registry.manifest(),
            "bridges": {
                "event_bus_attached": self.event_bus is not None,
                "service_container_attached": self.service_container is not None,
            },
            "metadata": dict(self.metadata),
        }

def create_workflow_core(**kwargs: Any) -> WorkflowCore:
    return WorkflowCore(**kwargs)
