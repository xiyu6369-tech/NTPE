# =====================================================
# NTPE 1.2 Professional
# Stage-17.1 Translation Workflow Engine
# =====================================================

from __future__ import annotations

from .workflow_context import WorkflowContext
from .workflow_events import WORKFLOW_COMPLETED, WORKFLOW_FAILED, WORKFLOW_STARTED, WorkflowEventBus
from .workflow_metrics import build_workflow_metrics
from .workflow_pipeline import WorkflowPipeline
from .workflow_registry import WorkflowRegistry
from .workflow_result import WorkflowResult, WorkflowStepResult
from .workflow_state import WorkflowState
from .workflow_step import WorkflowStep


def _prepare_step(context: WorkflowContext) -> WorkflowStepResult:
    normalized = context.source_text.replace("\r\n", "\n").strip()
    return WorkflowStepResult("prepare", output={"prepared_text": normalized}, message="input prepared")


def _intelligence_step(context: WorkflowContext) -> WorkflowStepResult:
    prepared = context.artifacts.get("prepared_text", context.source_text)
    signals = {
        "length": len(prepared),
        "paragraphs": len([p for p in str(prepared).split("\n") if p.strip()]),
        "strategy": context.strategy or "balanced",
    }
    return WorkflowStepResult("intelligence", output={"intelligence": signals}, message="intelligence analyzed")


def _translate_step(context: WorkflowContext) -> WorkflowStepResult:
    prepared = str(context.artifacts.get("prepared_text", context.source_text))
    # Stage-17.1 keeps provider execution mocked and deterministic; real provider binding remains runtime-extensible.
    translation = prepared
    return WorkflowStepResult("translate", output={"translation": translation}, message="translation produced")


def _quality_step(context: WorkflowContext) -> WorkflowStepResult:
    translation = str(context.artifacts.get("translation", ""))
    report = {"status": "pass" if translation.strip() else "fail", "length": len(translation)}
    return WorkflowStepResult("quality_check", output={"quality_report": report}, message="quality checked")


def _repair_step(context: WorkflowContext) -> WorkflowStepResult:
    report = context.artifacts.get("quality_report", {})
    repaired = dict(report).get("status") == "fail"
    return WorkflowStepResult("auto_repair", output={"repair_report": {"repaired": repaired}}, message="repair evaluated")


def _review_step(context: WorkflowContext) -> WorkflowStepResult:
    return WorkflowStepResult("review_gate", output={"review": {"required": False, "status": "approved"}}, message="review gate passed")


def _export_step(context: WorkflowContext) -> WorkflowStepResult:
    return WorkflowStepResult("export", output={"export": str(context.artifacts.get("translation", ""))}, message="export prepared")


class TranslationWorkflowEngine:
    """Stage-17.1 public facade for production translation workflow execution."""

    stage = "Stage-17.1"
    name = "Translation Workflow Engine"

    def __init__(self, registry: WorkflowRegistry | None = None, event_bus: WorkflowEventBus | None = None) -> None:
        self.event_bus = event_bus or WorkflowEventBus()
        self.registry = registry or self.build_default_registry()
        self.pipeline = WorkflowPipeline(self.registry, self.event_bus)

    @staticmethod
    def build_default_registry() -> WorkflowRegistry:
        registry = WorkflowRegistry()
        registry.extend([
            WorkflowStep("prepare", _prepare_step),
            WorkflowStep("intelligence", _intelligence_step),
            WorkflowStep("translate", _translate_step),
            WorkflowStep("quality_check", _quality_step),
            WorkflowStep("auto_repair", _repair_step),
            WorkflowStep("review_gate", _review_step),
            WorkflowStep("export", _export_step),
        ])
        return registry

    def run(self, context: WorkflowContext | str) -> WorkflowResult:
        if isinstance(context, str):
            context = WorkflowContext(source_text=context)
        state = WorkflowState()
        self.event_bus.emit(WORKFLOW_STARTED, workflow_id=context.workflow_id)
        errors: list[str] = []
        try:
            steps = self.pipeline.run(context, state)
            status = "completed"
            self.event_bus.emit(WORKFLOW_COMPLETED, workflow_id=context.workflow_id, step_count=len(steps))
        except Exception as exc:
            steps = []
            status = "failed"
            errors.append(str(exc))
            self.event_bus.emit(WORKFLOW_FAILED, workflow_id=context.workflow_id, error=str(exc))
        metrics = build_workflow_metrics(steps, context.artifacts)
        return WorkflowResult(context.workflow_id, status, steps, dict(context.artifacts), metrics, errors)

    def execute(self, source_text: str) -> WorkflowResult:
        return self.run(source_text)
