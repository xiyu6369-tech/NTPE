import subprocess
import sys


def test_lts_stable_complete_launcher_no_write_files():
    result = subprocess.run(
        [sys.executable, "ntpe_lts_stable_complete.py", "--no-write-files"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "NTPE 1.1 LTS Stable Release Complete" in result.stdout
    assert "validation: pass" in result.stdout
