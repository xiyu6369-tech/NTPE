from core.workflow.production_runtime_bridge import ProductionRuntimeBridge
from core.workflow.production_runtime_context import ProductionRuntimeContext
from core.workflow.production_runtime_integration import ProductionRuntimeIntegration


def test_stage17_7_runtime_executes_workflow():
    result = ProductionRuntimeIntegration().run("Hello")
    assert result.success
    assert result.artifacts["translation"] == "Hello"
    assert result.metrics["workflow_step_count"] >= 1


def test_stage17_7_runtime_accepts_optional_components():
    bridge = ProductionRuntimeBridge(
        resource_optimizer=lambda context: {"optimized": True, "runtime_id": context.runtime_id},
        scheduler=lambda context: {"scheduled": True, "workflow_id": context.workflow_id},
        review_layer=lambda workflow_result: {"reviewed": True, "status": "approved"},
        export_framework=lambda workflow_result: {"exported": True, "format": "txt"},
        dashboard_api=lambda payload: {"snapshot": True, "workflow_status": payload["workflow_status"]},
    )
    runtime = ProductionRuntimeIntegration(bridge=bridge)
    result = runtime.run(ProductionRuntimeContext(source_text="Hello", runtime_id="rt", workflow_id="wf"))
    assert result.success
    assert result.artifacts["resource_plan"]["optimized"] is True
    assert result.artifacts["schedule"]["scheduled"] is True
    assert result.artifacts["review_result"]["status"] == "approved"
    assert result.artifacts["export_result"]["exported"] is True
    assert result.artifacts["dashboard_snapshot"]["snapshot"] is True


def test_stage17_7_rejects_empty_input():
    result = ProductionRuntimeIntegration().run(ProductionRuntimeContext(source_text=""))
    assert not result.success
    assert result.status == "failed"
    assert result.errors
