from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    cmd = [sys.executable, "launcher_translate.py", "regression", "--set", "Test_Set_0", "--stage", "PS-04.2-integration", "--dry-run", "--overwrite"]
    proc = subprocess.run(cmd, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
    output = proc.stdout
    checks = [
        (proc.returncode == 0, "Regression dry run exits 0"),
        ("[NTPE PROGRESS]" in output, "Progress lines visible"),
        ("status: success" in output, "Regression status success"),
    ]
    failed = False
    print("NTPE PS-04.2 Integration Test")
    print("==============================")
    for ok, label in checks:
        print(f"{label:<30} {'PASS' if ok else 'FAIL'}")
        failed = failed or not ok
    print("PASS" if not failed else "FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
