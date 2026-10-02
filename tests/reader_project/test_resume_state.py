"""S9-03 reader-state derivation tests.

Hermetic: deterministic fake resume-state fixtures; no provider, no network,
no translation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.reader_project.manager import ReaderProjectManager
from core.reader_project.models import (
    BookRecord,
    OutputRecord,
    ReaderStatus,
)
from core.reader_project.state import derive_reader_status, derive_state, read_resume_state


def _setup(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_bytes(b"original source")
    manager = ReaderProjectManager(home=tmp_path / "NTPE_HOME")
    project = manager.create(source, title="雙月之夜")
    return manager, project, source


def _write_resume(tmp_path: Path, chunks: dict) -> Path:
    path = tmp_path / "novel_resume_state.json"
    path.write_text(json.dumps({"chunks": chunks}), encoding="utf-8")
    return path


def _artifact(tmp_path: Path) -> Path:
    path = tmp_path / "output" / "novel_zh.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("成品", encoding="utf-8")
    return path


def _chunks_success(n: int) -> dict:
    return {f"{i:06d}": {"status": "success"} for i in range(1, n + 1)}


# -- pure reader -----------------------------------------------------------

def test_read_resume_state_missing_is_not_started(tmp_path):
    assert read_resume_state(tmp_path / "nope.json") == (None, None)


def test_read_resume_state_corrupt(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    data, error = read_resume_state(path)
    assert data is None and error


# -- derivation ------------------------------------------------------------

def test_no_resume_no_artifact_is_not_started(tmp_path):
    _, project, _ = _setup(tmp_path)
    assert derive_reader_status(project) == ReaderStatus.NOT_STARTED


def test_partial_resume_is_resumable(tmp_path):
    manager, project, _ = _setup(tmp_path)
    resume = _write_resume(tmp_path, {**_chunks_success(47), "000048": {"status": "failed"}})
    project.execution.resume_state_path = str(resume)
    project.book = BookRecord(format="txt", title="x", total_units=120)
    manager.update(project, execution=project.execution, book=project.book)

    assert derive_reader_status(project) == ReaderStatus.RESUMABLE
    state = derive_state(project)
    assert state.completed_units == 47
    assert state.total_units == 120
    assert state.current_unit == 48
    assert state.reader_status == ReaderStatus.RESUMABLE.value


def test_all_success_with_artifact_is_completed(tmp_path):
    manager, project, _ = _setup(tmp_path)
    resume = _write_resume(tmp_path, _chunks_success(120))
    artifact = _artifact(tmp_path)
    project.book = BookRecord(format="txt", title="x", total_units=120)
    project.execution.resume_state_path = str(resume)
    project.output = OutputRecord(
        output_dir=str(artifact.parent),
        artifact_path=str(artifact),
        artifact_kind="txt",
        available=True,
    )
    manager.update(project, book=project.book, execution=project.execution, output=project.output)
    assert derive_reader_status(project) == ReaderStatus.COMPLETED


def test_artifact_exists_without_resume_is_completed(tmp_path):
    manager, project, _ = _setup(tmp_path)
    artifact = _artifact(tmp_path)
    project.output = OutputRecord(
        artifact_path=str(artifact), artifact_kind="txt", available=True
    )
    manager.update(project, output=project.output)
    assert derive_reader_status(project) == ReaderStatus.COMPLETED


def test_all_failed_no_artifact_is_failed(tmp_path):
    manager, project, _ = _setup(tmp_path)
    resume = _write_resume(tmp_path, {"000001": {"status": "failed"}})
    project.execution.resume_state_path = str(resume)
    manager.update(project, execution=project.execution)
    assert derive_reader_status(project) == ReaderStatus.FAILED


def test_changed_source_without_artifact_is_source_changed(tmp_path):
    manager, project, source = _setup(tmp_path)
    resume = _write_resume(tmp_path, _chunks_success(5))
    project.execution.resume_state_path = str(resume)
    manager.update(project, execution=project.execution)

    source.write_bytes(b"a completely different source")
    assert derive_reader_status(project) == ReaderStatus.SOURCE_CHANGED


def test_corrupt_resume_is_unrecoverable(tmp_path):
    manager, project, _ = _setup(tmp_path)
    resume = tmp_path / "novel_resume_state.json"
    resume.write_text("{broken", encoding="utf-8")
    project.execution.resume_state_path = str(resume)
    manager.update(project, execution=project.execution)
    assert derive_reader_status(project) == ReaderStatus.UNRECOVERABLE


def test_derive_state_does_not_write(tmp_path):
    manager, project, _ = _setup(tmp_path)
    before = manager.store.project_file(project.project_id).read_text(encoding="utf-8")
    derive_state(project)
    after = manager.store.project_file(project.project_id).read_text(encoding="utf-8")
    assert before == after


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
