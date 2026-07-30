import subprocess
import sys
from pathlib import Path


if __name__ == "__main__":
    tests = [
        "tests/unit/test_provider_failure_characterization.py",
        "tests/unit/test_provider_failure_review_api.py",
        "tests/integration/lcr_batch108_provider_failure_characterization_integration_test.py",
    ]
    raise SystemExit(subprocess.run([sys.executable, "-m", "pytest", *tests, "-q"], cwd=Path(__file__).parent).returncode)
