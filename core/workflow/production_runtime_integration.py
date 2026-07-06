# =====================================================
# NTPE 1.2 Professional
# Stage-17.7 Production Runtime Integration
# =====================================================

from __future__ import annotations

from typing import Any

from .production_runtime_bridge import ProductionRuntimeBridge
from .production_runtime_context import ProductionRuntimeContext
from .production_runtime_events import (
    PRODUCTION_RUNTIME_COMPLETED,
    PRODUCTION_RUNTIME_COMPONENT_BOUND,
    PRODUCTION_RUNTIME_FAILED,
    PRODUCTION_RUNTIME_STARTED,
    ProductionRuntimeEventBus,
)
from .production_runtime_metrics import build_production_runtime_metrics
from .production_runtime_result import ProductionRuntimeResult
from .workflow_engine import TranslationWorkflowEngine


class ProductionRuntimeIntegration:
    """Production execution facade for Stage-17 workflow modules.

    The integration is intentionally dependency-light. Components introduced by Stage-17.2 to Stage-17.6
    can be injected when present, while Stage-17.1 workflow execution remains fully compatible.
    """

    stage = "Stage-17.7"
    name = "Production Runtime Integration"

    def __init__(
        self,
        workflow_engine: TranslationWorkflowEngine | None = None,
        bridge: ProductionRuntimeBridge | None = None,
        event_bus: ProductionRuntimeEventBus | None = None,
    ) -> None:
        self.workflow_engine = workflow_engine or TranslationWorkflowEngine()
        self.bridge = bridge or ProductionRuntimeBridge()
        self.event_bus = event_bus or ProductionRuntimeEventBus()
        for component_name, component in self.bridge.components().items():
            if component is not None:
                self.event_bus.emit(PRODUCTION_RUNTIME_COMPONENT_BOUND, component=component_name)

    def run(self, context: ProductionRuntimeContext | str) -> ProductionRuntimeResult:
        if isinstance(context, str):
            context = ProductionRuntimeContext(source_text=context)
        errors: list[str] = []
        workflow_result: Any | None = None
        try:
            context.validate()
            self.event_bus.emit(PRODUCTION_RUNTIME_STARTED, runtime_id=context.runtime_id, workflow_id=context.workflow_id)
            context.update_artifacts({"resource_plan": self.bridge.optimize(context)})
            context.update_artifacts({"schedule": self.bridge.schedule(context)})
            workflow_context = context.to_workflow_context()
            workflow_result = self.workflow_engine.run(workflow_context)
            context.update_artifacts(dict(getattr(workflow_result, "artifacts", {}) or {}))
            context.update_artifacts({"review_result": self.bridge.review(workflow_result)})
            context.update_artifacts({"export_result": self.bridge.export(workflow_result)})
            dashboard_payload = {
                "runtime_id": context.runtime_id,
                "workflow_id": context.workflow_id,
                "workflow_status": getattr(workflow_result, "status", "unknown"),
                "artifacts": dict(context.artifacts),
            }
            context.update_artifacts({"dashboard_snapshot": self.bridge.snapshot(dashboard_payload)})
            status = "completed" if bool(getattr(workflow_result, "success", False)) else "failed"
            if status == "completed":
                self.event_bus.emit(PRODUCTION_RUNTIME_COMPLETED, runtime_id=context.runtime_id, workflow_id=context.workflow_id)
            else:
                message = "; ".join(getattr(workflow_result, "errors", []) or ["workflow did not complete"])
                errors.append(message)
                self.event_bus.emit(PRODUCTION_RUNTIME_FAILED, runtime_id=context.runtime_id, workflow_id=context.workflow_id, error=message)
        except Exception as exc:
            status = "failed"
            errors.append(str(exc))
            self.event_bus.emit(PRODUCTION_RUNTIME_FAILED, runtime_id=context.runtime_id, workflow_id=context.workflow_id, error=str(exc))
        events = self.event_bus.to_list()
        metrics = build_production_runtime_metrics(workflow_result, events, self.bridge.components())
        return ProductionRuntimeResult(
            runtime_id=context.runtime_id,
            workflow_id=context.workflow_id,
            status=status,
            workflow_result=workflow_result,
            artifacts=dict(context.artifacts),
            metrics=metrics,
            events=events,
            errors=errors,
        )

    def execute(self, source_text: str) -> ProductionRuntimeResult:
        return self.run(source_text)
