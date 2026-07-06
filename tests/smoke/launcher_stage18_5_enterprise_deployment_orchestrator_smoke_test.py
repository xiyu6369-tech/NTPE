from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# =====================================================
# NTPE 1.2 Professional
# Stage-18.5 Enterprise Deployment Orchestrator Smoke Test
# =====================================================

from core.enterprise.deployment_orchestrator import EnterpriseDeploymentOrchestrator


def main():
    result = EnterpriseDeploymentOrchestrator(root=".").prepare()
    assert result.success
    assert result.stage == "Stage-18.5"
    assert result.name == "Enterprise Deployment Orchestrator"
    print("PASS")


if __name__ == "__main__":
    main()
