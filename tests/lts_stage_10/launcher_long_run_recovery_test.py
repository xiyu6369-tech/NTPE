from __future__ import annotations

from pathlib import Path


def test_long_run_recovery_legacy_archived():
    """RM-4.3E: Verify legacy entrypoint present in archive/legacy_tools/."""
    archive_path = Path("archive/legacy_tools/ntpe_long_run_recovery.py")
    assert archive_path.exists(), f"Expected archived legacy tool at {archive_path}"
    content = archive_path.read_text(encoding="utf-8")
    assert "from lts.long_run_recovery import main" in content
    assert 'if __name__ == "__main__"' in content
