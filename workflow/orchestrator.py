"""Pipeline Orchestrator for NTPE 1.0 Beta Stage-09.2."""
from __future__ import annotations
from typing import Any, Callable

from .execution_plan import ExecutionPlan
from .pipeline_dispatcher import PipelineDispatcher
from .pipeline_models import PIPELINE_ORCHESTRATOR_STAGE, PIPELINE_ORCHESTRATOR_VERSION, PipelineDefinition
from .pipeline_registry import PipelineRegistry

class PipelineOrchestrator:
    version = PIPELINE_ORCHESTRATOR_VERSION
    stage = PIPELINE_ORCHESTRATOR_STAGE

    def __init__(self, *, event_bus: Any = None, service_container: Any = None, workflow_core: Any = None, job_scheduler: Any = None, runtime_bridge: Any = None, metadata: dict | None = None) -> None:
        self.registry = PipelineRegistry()
        self.dispatcher = PipelineDispatcher(event_bus=event_bus, service_container=service_container, workflow_core=workflow_core, job_scheduler=job_scheduler, runtime_bridge=runtime_bridge)
        self.event_bus = event_bus
        self.service_container = service_container
        self.workflow_core = workflow_core
        self.job_scheduler = job_scheduler
        self.runtime_bridge = runtime_bridge
        self.metadata = dict(metadata or {})

    def _publish(self, event_type: str, payload: dict) -> None:
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish(event_type, payload, topic="workflow.pipeline", source="pipeline_orchestrator")

    def create_pipeline(self, name: str, **metadata: Any) -> PipelineDefinition:
        pipeline = PipelineDefinition(name=name, metadata=dict(metadata))
        self._publish("pipeline.created", {"pipeline": name, "pipeline_id": pipeline.pipeline_id})
        self.registry.register(pipeline)
        self._publish("pipeline.registered", {"pipeline": name, "pipeline_id": pipeline.pipeline_id})
        return pipeline

    def register_pipeline(self, pipeline: PipelineDefinition) -> PipelineDefinition:
        registered = self.registry.register(pipeline)
        self._publish("pipeline.registered", {"pipeline": pipeline.name, "pipeline_id": pipeline.pipeline_id})
        return registered

    def add_stage(self, pipeline_name: str, stage_name: str, action: Callable[..., Any] | None = None, *, depends_on: list[str] | None = None, workflow_name: str | None = None, job_name: str | None = None, **metadata: Any) -> PipelineDefinition:
        pipeline = self.registry.get(pipeline_name)
        return pipeline.add_stage(stage_name, action, depends_on=depends_on, workflow_name=workflow_name, job_name=job_name, **metadata)

    def build_plan(self, pipeline_name: str) -> ExecutionPlan:
        return ExecutionPlan.build(self.registry.get(pipeline_name))

    def execute(self, pipeline_name: str, **payload: Any):
        return self.dispatcher.dispatch(self.registry.get(pipeline_name), **payload)

    def resume(self, pipeline_name: str, **payload: Any):
        self._publish("pipeline.resumed", {"pipeline": pipeline_name})
        return self.execute(pipeline_name, **payload)

    def manifest(self) -> dict:
        return {
            "version": self.version,
            "stage": self.stage,
            "foundation_status": "frozen",
            "integration_status": "frozen",
            "workflow_core_compatible": True,
            "job_scheduler_compatible": True,
            "additive_only": True,
            "registry": self.registry.manifest(),
            "bridges": {
                "event_bus_attached": self.event_bus is not None,
                "service_container_attached": self.service_container is not None,
                "workflow_core_attached": self.workflow_core is not None,
                "job_scheduler_attached": self.job_scheduler is not None,
                "runtime_bridge_attached": self.runtime_bridge is not None,
            },
            "metadata": dict(self.metadata),
        }

def create_pipeline_orchestrator(**kwargs: Any) -> PipelineOrchestrator:
    return PipelineOrchestrator(**kwargs)
