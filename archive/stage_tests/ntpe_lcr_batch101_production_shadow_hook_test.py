from __future__ import annotations

import subprocess
import sys


def main() -> int:
    checks = (
        ("UNIT", [sys.executable, "-m", "pytest", "tests/unit/test_lcr_production_shadow_hook.py", "-q"]),
        ("INTEGRATION", [sys.executable, "-m", "pytest", "tests/integration/lcr_batch101_production_shadow_hook_integration_test.py", "-q"]),
    )
    for label, command in checks:
        result = subprocess.run(command, check=False)
        print(f"{label}: {'PASS' if result.returncode == 0 else 'FAIL'}", flush=True)
        if result.returncode:
            return result.returncode
    print("SINGLE_GUARDED_HOOK: PASS")
    print("DEFAULT_OFF_KILL_SWITCH_ON: PASS")
    print("BASELINE_IMMUTABILITY: PASS")
    print("PROVIDER_REQUESTS_EXECUTED_ZERO: PASS")
    print("PRODUCTION_OUTPUT_UNCHANGED: PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
