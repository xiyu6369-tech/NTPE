from core.enterprise.config_center import EnterpriseConfigCenter, ConfigValidationError


def main() -> int:
    center = EnterpriseConfigCenter()
    config = center.load(environment="production")
    checks = [
        ("Loaded", bool(config)),
        ("Environment", config["enterprise"]["environment"] == "production"),
        ("Validated", center.validate()),
        ("Audit", center.audit()["stage"] == "Stage-18.2"),
        ("Export", '"enterprise"' in center.export()),
    ]
    center.register_provider("runtime", {"runtime": {"mode": "compatible"}})
    checks.append(("Registry", center.merged_registry_config()["runtime"]["mode"] == "compatible"))

    print("NTPE Stage-18.2 Enterprise Configuration Center Test")
    print("=" * 58)
    ok = True
    for name, passed in checks:
        ok = ok and passed
        print(f"{name:<18} {'PASS' if passed else 'FAIL'}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
