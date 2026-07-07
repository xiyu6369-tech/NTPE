import subprocess
import sys

result = subprocess.run([sys.executable, "launcher_translate.py", "corpus", "list"], text=True, capture_output=True, timeout=30)
assert result.returncode == 0, result.stdout + result.stderr
assert "Smoke_Set" in result.stdout
assert "Golden_Set" in result.stdout
assert "Regression_Set" in result.stdout
print("PASS")
