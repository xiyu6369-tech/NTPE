from core.enterprise.deployment_profile_manager import EnterpriseDeploymentProfileManager
from core.enterprise.deployment_profiles import DeploymentProfile


def main() -> int:
    manager = EnterpriseDeploymentProfileManager()
    profiles = manager.available_profiles()
    production = manager.resolve_profile("enterprise-controlled-host")
    audit = manager.audit_profile("enterprise-controlled-host")

    custom = DeploymentProfile(
        name="custom-imported",
        target="team-shared-runtime",
        environment="staging",
        enabled_capabilities=["shared_config", "audit_export"],
        config_overrides={"enterprise": {"deployment_profile": "custom-imported"}},
    )
    manager.register_profile(custom)

    checks = [
        ("Profiles", set(["local-workstation", "team-shared-runtime", "enterprise-controlled-host"]).issubset(set(profiles))),
        ("Production Env", production["enterprise"]["environment"] == "production"),
        ("Profile Name", production["enterprise"]["deployment_profile"] == "enterprise-controlled-host"),
        ("Capabilities", "config_lock" in production["enterprise"]["capabilities"]),
        ("Audit", audit["stage"] == "Stage-18.3" and len(audit["config_hash"]) == 64),
        ("Custom Profile", "custom-imported" in manager.available_profiles()),
        ("Manifest", manager.manifest()["status"] == "active"),
    ]

    print("NTPE Stage-18.3 Enterprise Deployment Profiles Test")
    print("=" * 58)
    ok = True
    for name, passed in checks:
        ok = ok and passed
        print(f"{name:<18} {'PASS' if passed else 'FAIL'}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
