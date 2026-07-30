import subprocess
import sys
from pathlib import Path


if __name__ == "__main__":
    tests = [
        "tests/unit/test_lcr_governance_baseline_consumption.py",
        "tests/integration/test_lcr_batch111_governance_baseline_consumption_audit.py",
    ]
    raise SystemExit(subprocess.run([sys.executable, "-m", "pytest", *tests, "-q"], cwd=Path(__file__).parent).returncode)
