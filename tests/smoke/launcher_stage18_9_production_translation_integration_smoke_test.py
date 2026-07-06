from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]

if __name__ == "__main__":
    result = subprocess.run(
        [sys.executable, "launcher_translate.py", "doctor"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    ok = result.returncode == 0 and "core_runtime" in result.stdout
    print("Stage-18.9 Smoke", "PASS" if ok else "FAIL")
    if not ok:
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(1)
