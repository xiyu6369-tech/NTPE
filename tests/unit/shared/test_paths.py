from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from core.shared.evidence.paths import (
    normalize_project_relative_path,
    require_path_within_root,
    resolve_project_relative_path,
)


def test_normal_path_and_windows_separator_are_deterministic() -> None:
    assert normalize_project_relative_path("audits/證據.json") == "audits/證據.json"
    assert normalize_project_relative_path(r"audits\batch3\證據.json") == "audits/batch3/證據.json"


@pytest.mark.parametrize(
    "value",
    [r"C:\evidence.txt", "D:/evidence.txt", "/evidence.txt", r"\\server\share\x", "../x", "a/../x", "a//x", "./x", "x\x00y", ""],
)
def test_unsafe_paths_are_rejected(value: str) -> None:
    with pytest.raises((TypeError, ValueError)):
        normalize_project_relative_path(value)


def test_missing_file_and_directory_policy(tmp_path: Path) -> None:
    directory = tmp_path / "evidence"
    directory.mkdir()
    assert resolve_project_relative_path(tmp_path, "missing.json") == tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError):
        resolve_project_relative_path(tmp_path, "missing.json", must_exist=True)
    with pytest.raises(IsADirectoryError):
        resolve_project_relative_path(tmp_path, "evidence", must_exist=True)
    assert resolve_project_relative_path(
        tmp_path, "evidence", must_exist=True, allow_directory=True
    ) == directory


def test_unicode_file_and_containment(tmp_path: Path) -> None:
    path = tmp_path / "證據.json"
    path.write_text("{}", encoding="utf-8")
    assert resolve_project_relative_path(tmp_path, "證據.json", must_exist=True) == path
    assert require_path_within_root(tmp_path, Path("證據.json")) == path
    with pytest.raises(ValueError):
        require_path_within_root(tmp_path, tmp_path.parent / "escape.json")


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "secret.txt").write_text("secret", encoding="utf-8")
    link = root / "link"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except OSError as exc:
        if sys.platform != "win32":
            pytest.skip(f"symlinks unavailable: {exc}")
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(outside)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip(f"links unavailable: {exc}; {result.stderr}")
    with pytest.raises(ValueError):
        resolve_project_relative_path(root, "link/secret.txt", must_exist=True)
