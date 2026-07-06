# =====================================================
# NTPE 1.2 Professional
# Stage-18.7 Enterprise Deployment Validation Test
# =====================================================

from core.enterprise.deployment_validation import EnterpriseDeploymentValidation


def check(name, condition):
    print(f"{name:<34} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    validator = EnterpriseDeploymentValidation(root=".")
    result = validator.validate("local-workstation")
    payload = result.to_dict()

    check("Validation Created", validator.stage == "Stage-18.7")
    check("Validation Ready", result.success)
    check("Baseline Modules", payload["checks"].get("baseline_modules") is True)
    check("Orchestrator Success", payload["checks"].get("orchestrator_success") is True)
    check("Gate Count", payload["checks"].get("gate_count") is True)
    check("All Gates Passed", payload["checks"].get("all_gates_passed") is True)
    check("Profile Match", payload["checks"].get("profile_match") is True)
    check("Additive Validation", payload["checks"].get("validation_additive") is True)
    check("Rollback Gate", any(g["name"] == "rollback_available" and g["passed"] for g in payload["gates"]))
    print("PASS")


if __name__ == "__main__":
    main()
