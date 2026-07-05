import subprocess
import sys


def test_lts_stable_finalization_launcher_no_write_files():
    result = subprocess.run(
        [sys.executable, "ntpe_lts_stable_finalization.py", "--no-write-files"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "NTPE 1.1 LTS Stable Release Finalization" in result.stdout
    assert "validation: pass" in result.stdout
