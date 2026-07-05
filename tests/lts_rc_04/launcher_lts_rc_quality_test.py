from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_lts_rc_quality_launcher_no_write_files_passes():
    completed = subprocess.run(
        [sys.executable, "ntpe_lts_rc_quality.py", "--no-write-files"],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "NTPE 1.1 LTS RC-04 Translation Quality / QA Validation" in completed.stdout
    assert "validation: pass" in completed.stdout
