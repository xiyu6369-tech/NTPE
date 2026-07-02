"""Pipeline dispatcher for NTPE Stage-09.2."""
from __future__ import annotations
from typing import Any, Dict
import time

from .execution_plan import ExecutionPlan
from .pipeline_context import PipelineContext
from .pipeline_models import (
    PipelineDefinition,
    PipelineExecutionResult,
    PipelineStage,
    PipelineStageResult,
    PipelineStageStatus,
    PipelineStatus,
)

class PipelineDispatcher:
    def __init__(self, *, event_bus: Any = None, service_container: Any = None, workflow_core: Any = None, job_scheduler: Any = None, runtime_bridge: Any = None) -> None:
        self.event_bus = event_bus
        self.service_container = service_container
        self.workflow_core = workflow_core
        self.job_scheduler = job_scheduler
        self.runtime_bridge = runtime_bridge

    def _publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish(event_type, payload, topic="workflow.pipeline", source="pipeline_dispatcher")

    def _run_stage(self, stage: PipelineStage, context: PipelineContext, payload: Dict[str, Any]) -> Any:
        if stage.action is not None:
            return stage.action(context=context, payload=payload, services=self.service_container)
        if stage.job_name and self.job_scheduler is not None:
            job = self.job_scheduler.schedule_job(stage.job_name, payload=payload, workflow_name=stage.workflow_name)
            return self.job_scheduler.run_next()
        if stage.workflow_name and self.workflow_core is not None:
            return self.workflow_core.execute(stage.workflow_name, **payload)
        if self.runtime_bridge is not None and hasattr(self.runtime_bridge, "execute"):
            return self.runtime_bridge.execute(stage.name, context=context, payload=payload)
        return {"stage": stage.name, "payload": dict(payload)}

    def dispatch(self, pipeline: PipelineDefinition, context: PipelineContext | None = None, **payload: Any) -> PipelineExecutionResult:
        context = context or PipelineContext(pipeline_id=pipeline.pipeline_id)
        result = PipelineExecutionResult(ok=False, pipeline_id=pipeline.pipeline_id, status=PipelineStatus.RUNNING)
        plan = ExecutionPlan.build(pipeline)
        if not plan.validate():
            result.status = PipelineStatus.FAILED
            result.errors.append("invalid execution plan")
            result.completed_at = time.time()
            return result

        pipeline.status = PipelineStatus.RUNNING
        self._publish("pipeline.started", {"pipeline": pipeline.name, "pipeline_id": pipeline.pipeline_id, "plan": plan.names()})
        try:
            for stage in plan.stages:
                stage.status = PipelineStageStatus.RUNNING
                stage_result = PipelineStageResult(name=stage.name, ok=False, status=stage.status)
                self._publish("pipeline.stage.started", {"pipeline": pipeline.name, "stage": stage.name})
                try:
                    output = self._run_stage(stage, context, dict(payload))
                    stage.status = PipelineStageStatus.COMPLETED
                    stage_result.ok = True
                    stage_result.status = stage.status
                    stage_result.output = output
                    result.outputs[stage.name] = output
                    context.set(stage.name, output)
                    self._publish("pipeline.stage.completed", {"pipeline": pipeline.name, "stage": stage.name})
                except Exception as exc:  # noqa: BLE001 - pipeline isolates stage failures
                    stage.status = PipelineStageStatus.FAILED
                    stage_result.ok = False
                    stage_result.status = stage.status
                    stage_result.error = str(exc)
                    result.errors.append(f"{stage.name}: {exc}")
                    self._publish("pipeline.stage.failed", {"pipeline": pipeline.name, "stage": stage.name, "error": str(exc)})
                    raise
                finally:
                    stage_result.completed_at = time.time()
                    result.stage_results[stage.name] = stage_result
            pipeline.status = PipelineStatus.COMPLETED
            result.ok = True
            result.status = PipelineStatus.COMPLETED
            self._publish("pipeline.completed", {"pipeline": pipeline.name, "pipeline_id": pipeline.pipeline_id})
        except Exception as exc:  # noqa: BLE001 - stable orchestrator error isolation
            pipeline.status = PipelineStatus.FAILED
            result.ok = False
            result.status = PipelineStatus.FAILED
            if not result.errors:
                result.errors.append(str(exc))
            self._publish("pipeline.failed", {"pipeline": pipeline.name, "error": str(exc)})
        finally:
            result.completed_at = time.time()
        return result
