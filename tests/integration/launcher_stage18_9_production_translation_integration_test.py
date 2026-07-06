from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]

if __name__ == "__main__":
    sample = ROOT / "input" / "stage18_9_integration_sample.txt"
    sample.parent.mkdir(exist_ok=True)
    sample.write_text("그는 조용히 문을 열었다.\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "launcher_translate.py", "txt", str(sample), "output", "--dry-run"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
    )
    ok = result.returncode == 0 and "status: success" in result.stdout
    print("Stage-18.9 Integration", "PASS" if ok else "FAIL")
    if not ok:
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(1)
