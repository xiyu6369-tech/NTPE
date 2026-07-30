import subprocess
import sys
from pathlib import Path


if __name__ == "__main__":
    tests = ["tests/integration/test_lcr_batch110_governance_freeze.py"]
    raise SystemExit(subprocess.run([sys.executable, "-m", "pytest", *tests, "-q"], cwd=Path(__file__).parent).returncode)
