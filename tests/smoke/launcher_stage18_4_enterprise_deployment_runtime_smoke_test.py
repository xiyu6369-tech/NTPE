from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# =====================================================
# NTPE 1.2 Professional
# Stage-18.4 Enterprise Deployment Runtime Smoke Test
# =====================================================

from core.enterprise.deployment_runtime import EnterpriseDeploymentRuntime


def main():
    result = EnterpriseDeploymentRuntime(root=".").prepare()
    assert result.success
    assert result.stage == "Stage-18.4"
    assert result.name == "Enterprise Deployment Runtime"
    print("PASS")


if __name__ == "__main__":
    main()
