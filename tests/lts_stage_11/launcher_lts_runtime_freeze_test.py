from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_lts_runtime_freeze_launcher(tmp_path: Path):
    result = subprocess.run(
        [sys.executable, "ntpe_lts_runtime_freeze.py", "--freeze-dir", str(tmp_path / "freeze")],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "status: frozen" in result.stdout
    assert (tmp_path / "freeze" / "LTS_Runtime_Freeze_Manifest_1_1.json").exists()
