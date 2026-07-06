from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.enterprise.config_center import EnterpriseConfigCenter


def main() -> int:
    center = EnterpriseConfigCenter(ROOT)
    config = center.load()
    ok = bool(config.get("enterprise")) and center.validate()
    print("NTPE Stage-18.2 Enterprise Configuration Center Smoke Test")
    print("=" * 62)
    print(f"Smoke {'PASS' if ok else 'FAIL'}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
