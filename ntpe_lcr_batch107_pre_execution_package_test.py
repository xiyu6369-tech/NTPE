import subprocess
import sys
from pathlib import Path


if __name__ == "__main__":
    tests = [
        "tests/unit/test_lcr_batch107_real_provider_validation.py",
        "tests/integration/lcr_batch107_pre_execution_package_integration_test.py",
    ]
    raise SystemExit(subprocess.run([sys.executable, "-m", "pytest", *tests, "-q"], cwd=Path(__file__).parent).returncode)
