from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.enterprise.config_center import EnterpriseConfigCenter


def main() -> int:
    center = EnterpriseConfigCenter(ROOT)
    config = center.load(environment="staging")
    exported = center.export(ROOT / "work" / "stage18_2_config_export.json")
    audit = center.audit()
    checks = [
        ("Config Center", center.stage == "Stage-18.2"),
        ("Environment", config["enterprise"]["environment"] == "staging"),
        ("Schema", center.validate(config)),
        ("Export", '"platform"' in exported),
        ("Audit", len(audit["config_hash"]) == 64),
    ]
    print("NTPE Stage-18.2 Enterprise Configuration Center Integration Test")
    print("=" * 68)
    ok = True
    for name, passed in checks:
        ok = ok and passed
        print(f"{name:<18} {'PASS' if passed else 'FAIL'}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
