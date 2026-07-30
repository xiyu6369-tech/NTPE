# =====================================================
# NTPE 1.2 Professional
# Stage-18.4 Enterprise Deployment Runtime Test
# =====================================================

from core.enterprise.deployment_runtime import EnterpriseDeploymentRuntime


def check(name, condition):
    print(f"{name:<34} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    runtime = EnterpriseDeploymentRuntime(root=".")
    result = runtime.prepare("local-workstation")
    payload = result.to_dict()

    check("Runtime Created", runtime.stage == "Stage-18.4")
    check("Runtime Ready", result.success)
    check("Context Profile", payload["context"]["profile"] == "local-workstation")
    check("Context Environment", payload["context"]["environment"] == "development")
    check("Runtime Plan", bool(payload["plan"]["steps"]))
    check("Rollback Plan", bool(payload["plan"]["rollback_steps"]))
    check("Additive Mode", payload["checks"].get("additive_mode") is True)
    check("Baseline Modules", payload["checks"].get("baseline_modules") is True)
    check("Profile Audit", bool(payload["details"].get("profile_audit", {}).get("config_hash")))
    check("Runtime Audit", bool(payload["details"].get("runtime_audit", {}).get("runtime_hash")))
    print("PASS")


if __name__ == "__main__":
    main()
