from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# =====================================================
# NTPE 1.2 Professional
# Stage-18.8 Enterprise Deployment Freeze Integration Test
# =====================================================

from core.enterprise.deployment_freeze import EnterpriseDeploymentFreeze


def main():
    freezer = EnterpriseDeploymentFreeze(root=ROOT)
    for profile in ["local-workstation", "team-shared-runtime", "enterprise-controlled-host"]:
        report = freezer.freeze(profile)
        payload = report.to_dict()
        assert report.success, payload
        assert payload["status"] == "frozen"
        assert payload["checks"]["validation_success"] is True
        assert payload["checks"]["all_freeze_gates"] is True
        assert payload["manifest"]["compatibility_rules"]["backward_compatible"] is True
        assert len(payload["freeze_gates"]) >= 5
    print("PASS")


if __name__ == "__main__":
    main()
