"""Safe project-relative paths for serialized evidence references."""

from __future__ import annotations

import ntpath
from pathlib import Path, PurePosixPath


def normalize_project_relative_path(value: str) -> str:
    """Normalize separators and validate a deterministic project-relative path."""
    if not isinstance(value, str):
        raise TypeError("project-relative path must be str")
    if not value or "\x00" in value:
        raise ValueError("project-relative path is empty or contains NUL")
    if value.startswith(("/", "\\")) or ntpath.isabs(value) or ntpath.splitdrive(value)[0]:
        raise ValueError(f"absolute or drive-qualified path is forbidden: {value!r}")
    normalized = value.replace("\\", "/")
    segments = normalized.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise ValueError(f"unsafe project-relative path: {value!r}")
    return PurePosixPath(*segments).as_posix()


def require_path_within_root(project_root: Path, candidate: Path) -> Path:
    """Resolve *candidate* and prove containment using pathlib semantics."""
    root = Path(project_root).resolve(strict=True)
    candidate_path = Path(candidate)
    if not candidate_path.is_absolute():
        candidate_path = root / candidate_path
    resolved = candidate_path.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {candidate}") from exc
    return resolved


def resolve_project_relative_path(
    project_root: Path,
    value: str,
    *,
    must_exist: bool = False,
    allow_directory: bool = False,
) -> Path:
    """Resolve a validated serialized path under *project_root*, including links."""
    root = Path(project_root).resolve(strict=True)
    relative = normalize_project_relative_path(value)
    candidate = root.joinpath(*PurePosixPath(relative).parts)
    resolved = require_path_within_root(root, candidate)
    if must_exist and not resolved.exists():
        raise FileNotFoundError(resolved)
    if resolved.exists() and resolved.is_dir() and not allow_directory:
        raise IsADirectoryError(resolved)
    return resolved
