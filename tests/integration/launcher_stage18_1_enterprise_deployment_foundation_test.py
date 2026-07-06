from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.enterprise.deployment_foundation import EnterpriseDeploymentFoundation


def main() -> int:
    result = EnterpriseDeploymentFoundation().audit()
    checks = [
        ("Ready", result.status == "ready"),
        ("Success", result.success),
        ("Baseline", result.checks["baseline_modules"]),
        ("Inventory", result.checks["package_inventory"]),
        ("Plan", result.checks["deployment_plan"]),
    ]
    print("NTPE Stage-18.1 Enterprise Deployment Foundation Integration Test")
    print("=" * 68)
    ok = True
    for name, passed in checks:
        ok = ok and passed
        print(f"{name:<18} {'PASS' if passed else 'FAIL'}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
