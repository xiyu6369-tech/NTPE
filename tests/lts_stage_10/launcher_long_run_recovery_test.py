from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_long_run_recovery_launcher(tmp_path: Path):
    output_dir = tmp_path / "output"
    (output_dir / "reports").mkdir(parents=True)
    result = subprocess.run(
        [sys.executable, "ntpe_long_run_recovery.py", str(output_dir), "--quiet"],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert (output_dir / "reports" / "Batch_Recovery_Plan.json").exists()
