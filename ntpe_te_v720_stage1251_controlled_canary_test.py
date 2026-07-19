import subprocess
import sys
from pathlib import Path


if __name__ == "__main__":
    tests = [
        "tests/unit/test_translation_quality_canary.py",
        "tests/integration/translation_engine_v720_stage1251_controlled_canary_test.py",
    ]
    raise SystemExit(subprocess.run([sys.executable, "-m", "pytest", *tests, "-q"], cwd=Path(__file__).parent).returncode)
