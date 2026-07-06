from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
result = subprocess.run(
    [sys.executable, "launcher_translate.py", "regression", "--set", "Test_Set_0", "--stage", "PS-03-smoke", "--dry-run", "--overwrite"],
    cwd=root,
    text=True,
    capture_output=True,
)
assert result.returncode == 0, result.stdout + result.stderr
assert "NTPE Literary Regression" in result.stdout
print("PASS")
