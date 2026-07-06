from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.enterprise.deployment_profile_manager import EnterpriseDeploymentProfileManager


def main() -> int:
    manager = EnterpriseDeploymentProfileManager()
    resolved = manager.resolve_profile("local-workstation")
    ok = resolved["enterprise"]["deployment_target"] == "local-workstation"
    print("NTPE Stage-18.3 Smoke Test")
    print("=" * 32)
    print(f"Deployment Profile      {'PASS' if ok else 'FAIL'}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
