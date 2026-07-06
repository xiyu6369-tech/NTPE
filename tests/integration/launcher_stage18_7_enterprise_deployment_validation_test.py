from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# =====================================================
# NTPE 1.2 Professional
# Stage-18.7 Enterprise Deployment Validation Integration Test
# =====================================================

from core.enterprise.deployment_validation import EnterpriseDeploymentValidation


def main():
    validator = EnterpriseDeploymentValidation(root=ROOT)
    results = validator.validate_all()
    assert set(results) == {"local-workstation", "team-shared-runtime", "enterprise-controlled-host"}
    for profile, result in results.items():
        payload = result.to_dict()
        assert result.success, payload
        assert payload["profile"] == profile
        assert payload["checks"]["all_gates_passed"] is True
        assert payload["checks"]["validation_additive"] is True
        assert len(payload["gates"]) >= 5
    print("PASS")


if __name__ == "__main__":
    main()
