from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.enterprise.deployment_runtime import EnterpriseDeploymentRuntime, EnterpriseRuntimeContext, EnterpriseRuntimePlan


def test_runtime_context_from_config():
    config = {"enterprise": {"deployment_profile": "local-workstation", "environment": "development", "deployment_target": "local-workstation", "capabilities": ["single_node"]}}
    context = EnterpriseRuntimeContext.from_config(config)
    assert context.profile == "local-workstation"
    assert context.environment == "development"
    assert context.target == "local-workstation"


def test_runtime_plan_from_context():
    context = EnterpriseRuntimeContext(profile="local-workstation", environment="development", target="local-workstation", root=".", capabilities=["rollback_plan"])
    plan = EnterpriseRuntimePlan.from_context(context)
    assert plan.execution_mode == "additive"
    assert "prepare_rollback_checkpoint" in plan.steps
    assert plan.rollback_steps


def test_runtime_prepare_success():
    result = EnterpriseDeploymentRuntime(root=".").prepare("local-workstation")
    assert result.success
    assert result.checks["baseline_modules"]
    assert result.details["runtime_audit"]["runtime_hash"]
