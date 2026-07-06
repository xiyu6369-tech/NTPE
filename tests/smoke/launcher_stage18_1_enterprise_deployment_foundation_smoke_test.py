from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.enterprise.deployment_foundation import EnterpriseDeploymentFoundation


def main() -> int:
    result = EnterpriseDeploymentFoundation().prepare("team-shared-runtime")
    ok = result.success and result.details["deployment_plan"]["target"] == "team-shared-runtime"
    print("NTPE Stage-18.1 Enterprise Deployment Foundation Smoke Test")
    print("=" * 64)
    print(f"Prepare {'PASS' if result.success else 'FAIL'}")
    print(f"Target  {'PASS' if result.details['deployment_plan']['target'] == 'team-shared-runtime' else 'FAIL'}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
