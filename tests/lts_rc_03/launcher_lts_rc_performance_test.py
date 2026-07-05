from __future__ import annotations

from lts.performance_validation import main


def test_lts_rc_performance_launcher_no_write():
    assert main(["--no-write-files", "--quiet"]) == 0
