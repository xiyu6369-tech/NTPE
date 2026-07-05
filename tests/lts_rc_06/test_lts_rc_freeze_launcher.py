from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_lts_rc_freeze_launcher_no_write_files_passes():
    completed = subprocess.run(
        [sys.executable, "ntpe_lts_rc_freeze.py", "--no-write-files"],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "NTPE 1.1 LTS RC-06 LTS RC Freeze" in completed.stdout
    assert "validation: pass" in completed.stdout
