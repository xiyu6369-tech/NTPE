"""Reader-facing state derivation (S9-03, S9 §8/§13/§15).

Maps runtime facts onto the reader state model. It only *reads* runtime
artifacts (``*_resume_state.json``, output artifact) — it never rewrites them
and never creates a translation job.

Both TXT and EPUB resume files share the same shape::

    {"chunks": {"<key>": {"status": "...", "source_hash": "...", ...}}}

so a single reader covers both formats (S9 §12).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .identity import source_changed
from .models import ReaderProject, ReaderStatus, StateRecord


SUCCESS_STATUSES = frozenset({"success", "pass_with_warning"})
FAILED_STATUSES = frozenset({"failed"})


def read_resume_state(path: str | Path | None) -> tuple[dict[str, Any] | None, str | None]:
    """Return ``(resume_state, error)``.

    * ``(None, None)``  no resume state (not started)
    * ``(data, None)``  readable resume state
    * ``(None, "<reason>")`` unreadable/corrupt resume state
    """
    if not path:
        return None, None
    file_path = Path(path)
    if not file_path.is_file():
        return None, None
    try:
        data = json.loads(file_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return None, str(exc)
    if not isinstance(data, dict) or not isinstance(data.get("chunks", {}), dict):
        return None, "resume state has an unexpected shape"
    return data, None


def _counts(resume_state: dict[str, Any]) -> tuple[int, int, int]:
    chunks = resume_state.get("chunks") or {}
    completed = 0
    failed = 0
    total = 0
    for entry in chunks.values():
        if not isinstance(entry, dict):
            continue
        status = str(entry.get("status", ""))
        if status == "dry_run":
            continue
        total += 1
        if status in SUCCESS_STATUSES:
            completed += 1
        elif status in FAILED_STATUSES:
            failed += 1
    return completed, failed, total


def derive_reader_status(project: ReaderProject) -> ReaderStatus:
    """Derive the reader status from persisted facts. Pure, no I/O writes."""
    resume_state, resume_error = read_resume_state(project.execution.resume_state_path)
    artifact_available = bool(
        project.output.available
        and project.output.artifact_path
        and Path(project.output.artifact_path).is_file()
    )

    if resume_error is not None:
        return ReaderStatus.UNRECOVERABLE

    if resume_state is None:
        return ReaderStatus.COMPLETED if artifact_available else ReaderStatus.NOT_STARTED

    completed, failed, total = _counts(resume_state)
    declared_total = int(project.book.total_units or project.state.total_units or 0)
    total = max(total, declared_total)

    changed = source_changed(project.source)

    if completed == 0 and failed == 0:
        return ReaderStatus.NOT_STARTED

    if failed > 0 and completed == 0 and not artifact_available:
        return ReaderStatus.FAILED

    if changed and not artifact_available:
        return ReaderStatus.SOURCE_CHANGED

    if artifact_available and total > 0 and completed >= total:
        return ReaderStatus.COMPLETED

    if artifact_available and failed > 0:
        return ReaderStatus.INCOMPLETE

    if completed > 0:
        return ReaderStatus.RESUMABLE

    return ReaderStatus.FAILED


def _first_incomplete_unit(resume_state: dict[str, Any] | None) -> int | None:
    if not resume_state:
        return None
    chunks = resume_state.get("chunks") or {}
    for key in sorted(chunks.keys(), key=_unit_sort_key):
        entry = chunks.get(key)
        status = str(entry.get("status", "")) if isinstance(entry, dict) else ""
        if status not in SUCCESS_STATUSES and status != "dry_run":
            return _unit_index(key)
    return None


def _unit_index(key: str) -> int | None:
    try:
        return int(str(key).split(":")[-1])
    except (TypeError, ValueError):
        return None


def _unit_sort_key(key: str) -> tuple[str, int]:
    idx = _unit_index(key)
    return (str(key), idx if idx is not None else 0)


def derive_state(project: ReaderProject) -> StateRecord:
    """Return a refreshed :class:`StateRecord` for the project."""
    resume_state, _ = read_resume_state(project.execution.resume_state_path)
    completed, failed, total = _counts(resume_state) if resume_state else (0, 0, 0)
    declared_total = int(project.book.total_units or project.state.total_units or 0)
    total = max(total, declared_total)

    last_error = project.state.last_error
    if failed > 0 and not last_error:
        last_error = f"{failed} segment(s) failed"

    # Recovery eligibility will be computed by the caller (manager/view_model)
    # and set on the state if needed. Default to False here.
    return StateRecord(
        reader_status=derive_reader_status(project).value,
        completed_units=completed,
        total_units=total,
        current_unit=_first_incomplete_unit(resume_state),
        last_error=last_error,
    )
