import subprocess
import sys


def test_lts_stable_preparation_launcher_no_write_files_passes():
    completed = subprocess.run(
        [sys.executable, "ntpe_lts_stable_preparation.py", "--no-write-files"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0
    assert "NTPE 1.1 LTS Stable Release Preparation" in completed.stdout
    assert "status: pass" in completed.stdout
