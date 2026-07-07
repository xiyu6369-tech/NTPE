import subprocess
import sys

result = subprocess.run(
    [sys.executable, "launcher_translate.py", "regression", "--set", "smoke", "--stage", "TER-v1-integration", "--dry-run", "--overwrite"],
    text=True,
    capture_output=True,
    timeout=60,
)
assert result.returncode == 0, result.stdout + result.stderr
assert "status: success" in result.stdout
print("PASS")
