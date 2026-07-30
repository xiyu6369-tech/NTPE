from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> int:
    sandbox = ROOT / ".ntpe_test_sandbox" / "tic_batch6_root" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/integration/tic_batch6_human_correction_root_cause_regression_test.py",
            "--basetemp",
            str(sandbox),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "28 passed" in result.stdout, result.stdout
    finally:
        shutil.rmtree(
            ROOT / ".ntpe_test_sandbox" / "tic_batch6_root", ignore_errors=True
        )
    statistics = json.loads(
        (ROOT / "artifacts/tic_batch6/TIC_BATCH6_STATISTICS.json").read_text(
            encoding="utf-8"
        )
    )
    assert statistics["failure_cases_processed"] == 2
    assert statistics["bad_translation_fail_count"] == 2
    print("TIC Batch 6 Human Correction, Root Cause, and Quality Regression ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
