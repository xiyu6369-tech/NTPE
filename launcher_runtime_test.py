from pathlib import Path

from core.runtime import RuntimeManager

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    rt = RuntimeManager(ROOT)

    checks = {
        "Runtime Dir": rt.runtime_dir.exists(),
        "Memory Dir": rt.memory_dir.exists(),
        "Reports Dir": rt.reports_dir.exists(),
        "Sessions Dir": rt.sessions_dir.exists(),
        "Translated Dir": rt.translated_dir.exists(),
        "Final Output Dir": rt.final_output_dir.exists(),
        "Logs Dir": rt.logs_dir.exists(),
        "Prompt Packages Dir": rt.prompt_packages_dir.exists(),
    }

    print("NTPE v1.2 Foundation Runtime Manager Test")
    print("=========================================")

    for name, ok in checks.items():
        print(f"{name:<22} {'PASS' if ok else 'FAIL'}")

    print(f"runtime: {rt.runtime_dir}")

    if not all(checks.values()):
        print("FAIL")
        raise SystemExit(2)

    print("PASS")