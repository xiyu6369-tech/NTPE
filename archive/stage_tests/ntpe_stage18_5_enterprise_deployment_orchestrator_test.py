# =====================================================
# NTPE 1.2 Professional
# Stage-18.5 Enterprise Deployment Orchestrator Test
# =====================================================

from core.enterprise.deployment_orchestrator import EnterpriseDeploymentOrchestrator


def check(name, condition):
    print(f"{name:<34} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    orchestrator = EnterpriseDeploymentOrchestrator(root=".")
    result = orchestrator.prepare("local-workstation")
    payload = result.to_dict()

    check("Orchestrator Created", orchestrator.stage == "Stage-18.5")
    check("Orchestrator Ready", result.success)
    check("Runtime Ready", payload["checks"].get("runtime_success") is True)
    check("Runtime Stage", payload["checks"].get("runtime_stage") is True)
    check("Additive Mode", payload["checks"].get("additive_mode") is True)
    check("Compatibility", payload["checks"].get("compatibility_contract") is True)
    check("Orchestration Plan", payload["checks"].get("orchestration_plan") is True)
    check("Rollback Available", payload["checks"].get("rollback_available") is True)
    check("Audit Hash", bool(payload["details"].get("orchestration_audit", {}).get("orchestration_hash")))
    print("PASS")


if __name__ == "__main__":
    main()
