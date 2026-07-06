from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
result = subprocess.run(
    [sys.executable, "launcher_translate.py", "corpus", "list"],
    cwd=root,
    text=True,
    capture_output=True,
)
assert result.returncode == 0, result.stdout + result.stderr
assert "Test_Set_0" in result.stdout
print("PASS")
