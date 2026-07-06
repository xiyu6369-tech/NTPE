from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# =====================================================
# NTPE 1.2 Professional
# Stage-18.5 Enterprise Deployment Orchestrator Integration Test
# =====================================================

from core.enterprise.deployment_orchestrator import EnterpriseDeploymentOrchestrator


def main():
    orchestrator = EnterpriseDeploymentOrchestrator(root=".")
    for profile in ["local-workstation", "team-shared-runtime", "enterprise-controlled-host"]:
        result = orchestrator.prepare(profile)
        assert result.success, result.to_dict()
        assert result.orchestration["profile"] == profile
        assert result.orchestration["mode"] == "additive"
        assert result.checks["orchestrator_compatibility"] is True
        assert result.details["orchestration_audit"]["orchestration_hash"]
    print("PASS")


if __name__ == "__main__":
    main()
