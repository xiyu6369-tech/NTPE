from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# =====================================================
# NTPE 1.2 Professional
# Stage-18.8 Enterprise Deployment Freeze Smoke Test
# =====================================================

from core.enterprise.deployment_freeze import EnterpriseDeploymentFreeze


def main():
    report = EnterpriseDeploymentFreeze(root=ROOT).freeze()
    assert report.success, report.to_dict()
    assert report.checks["all_freeze_gates"] is True
    print("PASS")


if __name__ == "__main__":
    main()
