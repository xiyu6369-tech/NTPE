from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# =====================================================
# NTPE 1.2 Professional
# Stage-18.7 Enterprise Deployment Validation Smoke Test
# =====================================================

from core.enterprise.deployment_validation import EnterpriseDeploymentValidation


def main():
    result = EnterpriseDeploymentValidation(root=ROOT).validate()
    assert result.success, result.to_dict()
    assert result.checks["all_gates_passed"] is True
    print("PASS")


if __name__ == "__main__":
    main()
