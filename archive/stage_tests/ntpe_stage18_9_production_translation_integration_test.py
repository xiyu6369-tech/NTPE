from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def run(cmd):
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=60)


if __name__ == "__main__":
    print("NTPE Stage-18.9 Production Translation Integration Test")
    print("=======================================================")
    checks = []
    checks.append(("Launcher Exists", (ROOT / "launcher_translate.py").exists()))
    checks.append(("Production CLI Exists", (ROOT / "ntpe_production_translate.py").exists()))
    checks.append(("Input Folder", (ROOT / "input").exists()))
    checks.append(("Output Folder", (ROOT / "output").exists()))
    doctor = run([sys.executable, "launcher_translate.py", "doctor"])
    checks.append(("Doctor Command", doctor.returncode == 0 and "core_runtime" in doctor.stdout))
    sample = ROOT / "input" / "stage18_9_sample.txt"
    sample.write_text("안녕하세요. 이것은 번역 통합 테스트입니다.\n", encoding="utf-8")
    dry = run([sys.executable, "launcher_translate.py", "txt", str(sample), "output", "--dry-run"])
    checks.append(("TXT Dry Run", dry.returncode == 0 and "status: success" in dry.stdout))
    for name, ok in checks:
        print(f"{name:<24} {'PASS' if ok else 'FAIL'}")
    if not all(ok for _, ok in checks):
        print(doctor.stdout)
        print(doctor.stderr)
        print(dry.stdout)
        print(dry.stderr)
        raise SystemExit(1)
    print("PASS")
