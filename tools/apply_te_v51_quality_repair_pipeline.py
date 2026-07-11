from pathlib import Path

root = Path(__file__).resolve().parents[1]
package = root / "core" / "translation_quality_v5"
target_init = package / "__init__.py"
staged_init = package / "__init__.py.stage510"

if not package.exists():
    raise SystemExit(f"Missing TE v5.0 package: {package}")
if not staged_init.exists():
    raise SystemExit(f"Missing staged init: {staged_init}")

required = [
    package / "quality_repair_planner.py",
    package / "quality_retry_orchestrator.py",
    package / "quality_chunk_rebuild_planner.py",
    package / "quality_repair_pipeline.py",
]
missing = [str(path) for path in required if not path.exists()]
if missing:
    raise SystemExit("Missing TE v5.1 files:\n" + "\n".join(missing))

if target_init.exists():
    backup = target_init.with_suffix(target_init.suffix + ".stage510.bak")
    backup.write_text(target_init.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"BACKUP: {backup}")

target_init.write_text(staged_init.read_text(encoding="utf-8"), encoding="utf-8")
staged_init.unlink()
print(f"UPDATED: {target_init}")
print("TE v5.1 Quality Repair Pipeline Milestone applied.")
print("No Translation Runtime, Provider Runtime, launcher, Prompt, Context, or Naturalness Guard file was modified.")
