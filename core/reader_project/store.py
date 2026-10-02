"""Project storage (S9-02, S9 §19/§20).

Storage root resolution is per-user and never CWD/repo-relative, so a reader
can launch NTPE from anywhere and still find their projects.

Layout::

    <NTPE_HOME>/projects/<project_id>/project.json

All writes are atomic (temp file + ``os.replace``) to avoid half-written
Project state.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any


PROJECT_FILE_NAME = "project.json"
PROJECTS_DIR_NAME = "projects"


def resolve_ntpe_home(env: Mapping[str, str] | None = None) -> Path:
    """Resolve the per-user NTPE data root.

    Precedence:
      1. ``NTPE_HOME`` (explicit override, used verbatim)
      2. Windows: ``%LOCALAPPDATA%\\NTPE``
      3. XDG: ``$XDG_DATA_HOME/NTPE``
      4. fallback: ``~/.ntpe``
    """
    env = os.environ if env is None else env

    override = env.get("NTPE_HOME")
    if override:
        return Path(override).expanduser().resolve()

    if os.name == "nt":
        local_appdata = env.get("LOCALAPPDATA")
        if local_appdata:
            return (Path(local_appdata) / "NTPE").resolve()

    xdg = env.get("XDG_DATA_HOME")
    if xdg:
        return (Path(xdg) / "NTPE").resolve()

    return (Path.home() / ".ntpe").resolve()


class ProjectStore:
    """Filesystem store for Reader Projects."""

    def __init__(self, home: str | Path | None = None):
        self.home = Path(home).expanduser().resolve() if home else resolve_ntpe_home()
        self.projects_root = self.home / PROJECTS_DIR_NAME

    def project_dir(self, project_id: str) -> Path:
        safe = str(project_id).strip()
        if not safe or any(sep in safe for sep in ("/", "\\", "..")):
            raise ValueError(f"invalid project_id: {project_id!r}")
        return self.projects_root / safe

    def project_file(self, project_id: str) -> Path:
        return self.project_dir(project_id) / PROJECT_FILE_NAME

    def exists(self, project_id: str) -> bool:
        return self.project_file(project_id).is_file()

    def read_raw(self, project_id: str) -> dict[str, Any]:
        path = self.project_file(project_id)
        if not path.is_file():
            raise FileNotFoundError(f"project not found: {project_id}")
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError(f"invalid project payload: {path}")
        return data

    def read_from_path(self, path: str | Path) -> dict[str, Any]:
        file_path = Path(path)
        if not file_path.is_file():
            raise FileNotFoundError(f"project not found: {file_path}")
        data = json.loads(file_path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError(f"invalid project payload: {file_path}")
        return data

    def write(self, project_id: str, payload: dict[str, Any]) -> Path:
        path = self.project_file(project_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(path, payload)
        return path

    def delete(self, project_id: str) -> bool:
        directory = self.project_dir(project_id)
        if not directory.is_dir():
            return False
        for child in sorted(directory.rglob("*"), reverse=True):
            if child.is_file() or child.is_symlink():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        directory.rmdir()
        return True

    def list_project_files(self) -> list[Path]:
        if not self.projects_root.is_dir():
            return []
        return sorted(
            child / PROJECT_FILE_NAME
            for child in self.projects_root.iterdir()
            if child.is_dir() and (child / PROJECT_FILE_NAME).is_file()
        )


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON atomically: temp file in the same dir, then os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
