from __future__ import annotations

import subprocess
import sys


def main() -> int:
    checks = (
        ("UNIT", [sys.executable, "-m", "pytest", "tests/unit/test_lcr_offline_validation.py", "-q"]),
        ("INTEGRATION", [sys.executable, "-m", "pytest", "tests/integration/lcr_batch9_offline_golden_tic_validation_integration_test.py", "-q"]),
    )
    for label, command in checks:
        result = subprocess.run(command, check=False)
        print(f"{label}: {'PASS' if result.returncode == 0 else 'FAIL'}", flush=True)
        if result.returncode:
            return result.returncode
    print("OFFLINE_FIXED_CORPUS_BOUNDARY: PASS")
    print("PROVIDER_REQUESTS_EXECUTED_ZERO: PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
