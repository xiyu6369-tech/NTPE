# =====================================================
# NTPE 1.2 Professional
# Stage-17.3 Resource Optimizer Integration Test
# =====================================================

from core.workflow.resource_bridge import optimize_workflow_resources
from core.workflow.resource_profile import ResourceProfile
from core.workflow.workflow_context import WorkflowContext


def test_resource_optimizer_binds_to_workflow_context():
    context = WorkflowContext(source_text="hello world" * 20, metadata={"cache_hit_rate": 0.25, "max_workers": 2})
    result = optimize_workflow_resources(context, profiles=[ResourceProfile(provider="local", model="tiny", cost_per_1k_tokens=0.0)])
    assert result.success
    assert context.artifacts["resource_plan"]["provider"] == "local"
    assert context.history[-1]["step"] == "resource_optimizer"
