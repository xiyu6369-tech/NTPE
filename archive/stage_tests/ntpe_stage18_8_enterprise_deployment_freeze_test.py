# =====================================================
# NTPE 1.2 Professional
# Stage-18.8 Enterprise Deployment Freeze Test
# =====================================================

from core.enterprise.deployment_freeze import EnterpriseDeploymentFreeze


def check(name, condition):
    print(f"{name:<34} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    freezer = EnterpriseDeploymentFreeze(root=".")
    report = freezer.freeze("local-workstation")
    payload = report.to_dict()

    check("Freeze Created", freezer.stage == "Stage-18.8")
    check("Freeze Success", report.success)
    check("Freeze Status", payload["status"] == "frozen")
    check("Manifest Frozen", payload["manifest"]["status"] == "frozen")
    check("Manifest Hash", bool(payload["manifest"]["manifest_hash"]))
    check("Validation Success", payload["checks"].get("validation_success") is True)
    check("Required Modules", payload["checks"].get("all_required_modules") is True)
    check("Freeze Gates", payload["checks"].get("all_freeze_gates") is True)
    check("Additive Contract", payload["checks"].get("additive_contract") is True)
    check("Backward Compatible", payload["checks"].get("backward_compatible") is True)
    print("PASS")


if __name__ == "__main__":
    main()
