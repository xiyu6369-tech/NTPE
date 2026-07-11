from pathlib import Path

root = Path(__file__).resolve().parents[1]
package = root / "core" / "translation_quality_v5"
target_init = package / "__init__.py"
staged_init = package / "__init__.py.stage520"

if not package.exists():
    raise SystemExit(f"Missing TE v5 package: {package}")
if not staged_init.exists():
    raise SystemExit(f"Missing staged init: {staged_init}")

required = [
    package / "quality_runtime_gate_contract.py",
    package / "quality_runtime_gate_admission.py",
    package / "quality_runtime_gate_decision.py",
    package / "quality_runtime_gate_pilot.py",
]
missing = [str(path) for path in required if not path.exists()]
if missing:
    raise SystemExit("Missing TE v5.2 files:\n" + "\n".join(missing))

if target_init.exists():
    backup = target_init.with_suffix(target_init.suffix + ".stage520.bak")
    backup.write_text(target_init.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"BACKUP: {backup}")

target_init.write_text(staged_init.read_text(encoding="utf-8"), encoding="utf-8")
staged_init.unlink()
print(f"UPDATED: {target_init}")
print("TE v5.2 Quality Runtime Gate Pilot Milestone applied.")
print("No Translation Runtime, Provider Runtime, launcher, Prompt, Context, or Naturalness Guard file was modified.")
