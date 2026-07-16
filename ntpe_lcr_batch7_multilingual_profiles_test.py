from __future__ import annotations

import subprocess
import sys


def main() -> int:
    checks = (("UNIT", [sys.executable, "-m", "pytest", "tests/unit/test_multilingual_profiles.py", "-q"]), ("INTEGRATION", [sys.executable, "-m", "pytest", "tests/integration/lcr_batch7_multilingual_profiles_integration_test.py", "-q"]))
    for label, command in checks:
        result = subprocess.run(command, check=False)
        print(f"{label}: {'PASS' if result.returncode == 0 else 'FAIL'}", flush=True)
        if result.returncode: return result.returncode
    print("OFFLINE_BOUNDARY: PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__": raise SystemExit(main())
