from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> int:
    sandbox = ROOT / ".ntpe_test_sandbox" / "tic_batch61_root" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/integration/tic_batch61_human_approval_regression_activation_test.py",
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
        assert "31 passed" in result.stdout, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "tic_batch61_root", ignore_errors=True)
    statistics = json.loads(
        (ROOT / "artifacts/tic_batch61/TIC_BATCH61_STATISTICS.json").read_text(encoding="utf-8")
    )
    assert statistics["approvals_created"] == 2
    assert statistics["active_regressions"] == 2
    assert statistics["pending_regressions"] == 0
    print("TIC Batch 6.1 Human Approval and Regression Activation ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
