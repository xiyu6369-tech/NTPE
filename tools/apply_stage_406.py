
from pathlib import Path

root = Path(__file__).resolve().parents[1]
package = root / "core" / "translation_reliability"
target_init = package / "__init__.py"
staged_init = package / "__init__.py.stage406"

if not package.exists():
    raise SystemExit(f"Missing package: {package}")
if not staged_init.exists():
    raise SystemExit(f"Missing staged init file: {staged_init}")

if target_init.exists():
    backup = target_init.with_suffix(target_init.suffix + ".stage406.bak")
    backup.write_text(target_init.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"BACKUP: {backup}")

target_init.write_text(staged_init.read_text(encoding="utf-8"), encoding="utf-8")
staged_init.unlink()
print(f"UPDATED: {target_init}")
print("TE v4.0 Stage-4.0.6 applied.")
