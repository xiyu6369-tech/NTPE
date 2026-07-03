from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_lts_release_candidate_launcher(tmp_path: Path):
    result = subprocess.run(
        [sys.executable, "ntpe_lts_release_candidate.py", "--rc-dir", str(tmp_path / "rc")],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "status: ready" in result.stdout
    assert "validation: pass" in result.stdout
    assert (tmp_path / "rc" / "LTS_Release_Candidate_Manifest_1_1.json").exists()
