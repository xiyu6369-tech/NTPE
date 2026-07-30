from __future__ import annotations

import subprocess
import sys


def main() -> int:
    checks = [
        ("UNIT", [sys.executable, "-m", "pytest", "tests/unit/test_post_polish_semantic_verification.py", "-q"]),
        ("INTEGRATION", [sys.executable, "-m", "pytest", "tests/integration/lcr_batch6_post_polish_semantic_verification_integration_test.py", "-q"]),
    ]
    for label, command in checks:
        completed = subprocess.run(command, check=False)
        print(f"{label}: {'PASS' if completed.returncode == 0 else 'FAIL'}", flush=True)
        if completed.returncode:
            return completed.returncode
    print("OFFLINE_BOUNDARY: PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
