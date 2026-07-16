from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> int:
    commands = (
        [sys.executable, "-m", "pytest", "tests/unit/test_lcr_character_memory_shadow.py", "-q"],
        [sys.executable, "-m", "pytest", "tests/integration/lcr_batch102_character_memory_shadow_integration_test.py", "-q"],
    )
    for command in commands:
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return result.returncode
    print("LCR Batch 10.2 Character Memory Shadow: ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
