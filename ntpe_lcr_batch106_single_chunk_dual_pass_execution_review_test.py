import subprocess
import sys
from pathlib import Path


if __name__ == "__main__":
    tests = [
        "tests/unit/test_lcr_single_chunk_execution_authorization.py",
        "tests/unit/test_lcr_single_chunk_dual_pass_executor.py",
        "tests/unit/test_lcr_review_candidate_artifact.py",
        "tests/integration/lcr_batch106_single_chunk_execution_review_integration_test.py",
    ]
    raise SystemExit(subprocess.run([sys.executable, "-m", "pytest", *tests, "-q"], cwd=Path(__file__).parent).returncode)
