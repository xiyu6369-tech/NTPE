from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# =====================================================
# NTPE 1.2 Professional
# Stage-18.4 Enterprise Deployment Runtime Integration Test
# =====================================================

from core.enterprise.deployment_runtime import EnterpriseDeploymentRuntime


def main():
    runtime = EnterpriseDeploymentRuntime(root=".")
    for profile in ["local-workstation", "team-shared-runtime", "enterprise-controlled-host"]:
        result = runtime.prepare(profile)
        assert result.success, result.to_dict()
        assert result.context["profile"] == profile
        assert result.plan["execution_mode"] == "additive"
        assert result.checks["compatibility_contract"] is True
    print("PASS")


if __name__ == "__main__":
    main()
