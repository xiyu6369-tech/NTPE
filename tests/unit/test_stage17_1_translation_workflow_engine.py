from core.workflow import TranslationWorkflowEngine, WorkflowContext, WorkflowRegistry, WorkflowStep
from core.workflow.workflow_result import WorkflowStepResult


def test_default_workflow_runs_all_steps():
    engine = TranslationWorkflowEngine()
    result = engine.run("第一段。\n第二段。")
    assert result.success
    assert result.metrics["completed_step_count"] == 7
    assert result.artifacts["export"] == "第一段。\n第二段。"
    assert result.artifacts["quality_report"]["status"] == "pass"


def test_workflow_context_preserves_metadata_and_history():
    engine = TranslationWorkflowEngine()
    context = WorkflowContext(source_text="測試", workflow_id="wf-1", metadata={"book": "demo"})
    result = engine.run(context)
    assert result.workflow_id == "wf-1"
    assert context.metadata["book"] == "demo"
    assert len(context.history) == 7


def test_custom_registry_supports_extension_steps():
    registry = WorkflowRegistry()
    registry.register(WorkflowStep("custom", lambda ctx: WorkflowStepResult("custom", output={"custom": True})))
    engine = TranslationWorkflowEngine(registry=registry)
    result = engine.run("abc")
    assert result.success
    assert result.artifacts["custom"] is True
