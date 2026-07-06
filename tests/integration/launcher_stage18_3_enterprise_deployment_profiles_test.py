from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.enterprise.deployment_profile_manager import EnterpriseDeploymentProfileManager


def main() -> int:
    manager = EnterpriseDeploymentProfileManager()
    checks = []
    for profile in manager.available_profiles():
        resolved = manager.resolve_profile(profile)
        checks.append((profile, resolved["enterprise"]["deployment_profile"] == profile))
    checks.append(("audit", manager.audit_profile("team-shared-runtime")["validated"] is True))

    print("NTPE Stage-18.3 Integration Launcher")
    print("=" * 42)
    ok = True
    for name, passed in checks:
        ok = ok and passed
        print(f"{name:<28} {'PASS' if passed else 'FAIL'}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
