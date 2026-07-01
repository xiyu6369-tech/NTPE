from pathlib import Path

ROOT = Path(__file__).resolve().parent
PIPELINE = ROOT / "engine" / "pipeline" / "pipeline_v1.py"

if __name__ == "__main__":
    text = PIPELINE.read_text(encoding="utf-8-sig")

    checks = {
        "RuntimeManager import": "from core.runtime import RuntimeManager" in text,
        "Runtime instance": "self.runtime = RuntimeManager(self.root)" in text,
        "Runtime log path": "self.runtime.log_path(" in text,
        "Runtime report path": "self.runtime.report_path(" in text,
        "Runtime session path": "self.runtime.session_path(" in text,
        "Runtime translated path": "self.runtime.translated_path(" in text,
        "Runtime prompt package path": "self.runtime.prompt_package_path(" in text,
    }

    print("NTPE v1.2 Foundation Runtime Migration Test")
    print("===========================================")

    for name, ok in checks.items():
        print(f"{name:<30} {'PASS' if ok else 'FAIL'}")

    if not all(checks.values()):
        print("FAIL")
        raise SystemExit(2)

    print("PASS")