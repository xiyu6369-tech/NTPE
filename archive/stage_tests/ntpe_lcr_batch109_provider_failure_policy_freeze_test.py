import subprocess
import sys
from pathlib import Path


if __name__ == "__main__":
    tests = ["tests/integration/test_lcr_batch109_provider_failure_policy_freeze.py"]
    raise SystemExit(subprocess.run([sys.executable, "-m", "pytest", *tests, "-q"], cwd=Path(__file__).parent).returncode)
