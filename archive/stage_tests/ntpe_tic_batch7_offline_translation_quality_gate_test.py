from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> int:
    sandbox = ROOT / ".ntpe_test_sandbox" / "tic_batch7_root" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/integration/tic_batch7_offline_translation_quality_gate_test.py", "--basetemp", str(sandbox)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "passed" in result.stdout and "failed" not in result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "tic_batch7_root", ignore_errors=True)
    statistics = json.loads((ROOT / "artifacts/tic_batch7/TIC_BATCH7_STATISTICS.json").read_text(encoding="utf-8"))
    assert statistics["active_regressions_loaded"] == 2
    assert statistics["quality_candidates_allowed"] == 2
    print("TIC Batch 7 Offline Translation Quality Gate Integration ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
