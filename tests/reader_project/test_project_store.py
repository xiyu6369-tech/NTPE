"""S9-02 Project persistence tests.

Hermetic: ``NTPE_HOME`` is a tmp dir; no provider, no network, no translation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.reader_project.manager import (
    ProjectError,
    ProjectNotFoundError,
    ProjectSchemaError,
    ReaderProjectManager,
)
from core.reader_project.models import (
    SCHEMA_VERSION,
    BookRecord,
    OutputRecord,
    ReaderStatus,
    StateRecord,
)
from core.reader_project.store import ProjectStore, resolve_ntpe_home


def _manager(tmp_path: Path) -> ReaderProjectManager:
    return ReaderProjectManager(home=tmp_path / "NTPE_HOME")


def _txt(tmp_path: Path, name: str = "novel.txt", body: bytes = b"source text") -> Path:
    path = tmp_path / name
    path.write_bytes(body)
    return path


# -- create / load ---------------------------------------------------------

def test_create_writes_schema_versioned_project(tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_txt(tmp_path), title="雙月之夜")

    assert project.project_schema_version == SCHEMA_VERSION
    assert project.project_id
    assert project.state.reader_status == ReaderStatus.NOT_STARTED.value
    assert project.book.format == "txt"
    assert project.execution.pipeline_mode == "runtime"
    assert project.created_at and project.updated_at and project.last_activity_at

    project_file = manager.store.project_file(project.project_id)
    assert project_file.is_file()
    payload = json.loads(project_file.read_text(encoding="utf-8"))
    assert payload["project_schema_version"] == SCHEMA_VERSION
    assert payload["source"]["hash"]


def test_create_epub_sets_pipeline_mode(tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_txt(tmp_path, "book.epub", b"PK\x03\x04epub"), format="epub")
    assert project.book.format == "epub"
    assert project.execution.pipeline_mode == "epub"


def test_load_round_trips(tmp_path):
    manager = _manager(tmp_path)
    created = manager.create(_txt(tmp_path), title="Novel")
    loaded = manager.load(created.project_id)
    assert loaded.to_dict() == created.to_dict()


def test_load_missing_raises_not_found(tmp_path):
    manager = _manager(tmp_path)
    with pytest.raises(ProjectNotFoundError):
        manager.load("does-not-exist")


# -- update / save ---------------------------------------------------------

def test_update_persists_state_and_touches_activity(tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_txt(tmp_path))
    before = project.updated_at

    updated = manager.update(
        project,
        state=StateRecord(
            reader_status=ReaderStatus.RESUMABLE.value,
            completed_units=47,
            total_units=120,
            current_unit=48,
        ),
        book=BookRecord(format="txt", title="雙月之夜", total_units=120),
    )
    assert updated.state.completed_units == 47
    assert updated.last_activity_at >= before

    reloaded = manager.load(project.project_id)
    assert reloaded.state.reader_status == ReaderStatus.RESUMABLE.value
    assert reloaded.state.completed_units == 47
    assert reloaded.book.total_units == 120


def test_output_reference_is_persisted_not_guessed(tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_txt(tmp_path))
    artifact = tmp_path / "output" / "novel_zh.txt"
    manager.update(
        project,
        output=OutputRecord(
            output_dir=str(artifact.parent),
            artifact_path=str(artifact),
            artifact_kind="txt",
            available=True,
        ),
    )
    reloaded = manager.load(project.project_id)
    assert reloaded.output.artifact_path == str(artifact)
    assert reloaded.output.available is True


# -- list ------------------------------------------------------------------

def test_list_projects_returns_created(tmp_path):
    manager = _manager(tmp_path)
    a = manager.create(_txt(tmp_path, "a.txt"), title="A")
    b = manager.create(_txt(tmp_path, "b.txt"), title="B")
    listed = {p.project_id for p in manager.list_projects()}
    assert {a.project_id, b.project_id} <= listed


def test_list_projects_skips_corrupt_project(tmp_path):
    manager = _manager(tmp_path)
    good = manager.create(_txt(tmp_path), title="Good")
    bad_dir = manager.store.projects_root / "corrupt"
    bad_dir.mkdir(parents=True)
    (bad_dir / "project.json").write_text("{not json", encoding="utf-8")

    listed = manager.list_projects()
    assert [p.project_id for p in listed] == [good.project_id]


def test_list_projects_empty_when_no_root(tmp_path):
    manager = _manager(tmp_path)
    assert manager.list_projects() == []


# -- schema versioning -----------------------------------------------------

def test_newer_schema_is_rejected(tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_txt(tmp_path))
    path = manager.store.project_file(project.project_id)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["project_schema_version"] = SCHEMA_VERSION + 1
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ProjectSchemaError):
        manager.load(project.project_id)


def test_missing_schema_version_is_rejected(tmp_path):
    manager = _manager(tmp_path)
    project_dir = manager.store.project_dir("legacy")
    project_dir.mkdir(parents=True)
    (project_dir / "project.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ProjectSchemaError):
        manager.load("legacy")


# -- delete ----------------------------------------------------------------

def test_delete_requires_confirmation(tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_txt(tmp_path))
    with pytest.raises(ProjectError):
        manager.delete(project.project_id)
    assert manager.exists(project.project_id)


def test_delete_is_scoped_to_one_project(tmp_path):
    manager = _manager(tmp_path)
    keep = manager.create(_txt(tmp_path, "keep.txt"))
    remove = manager.create(_txt(tmp_path, "remove.txt"))

    assert manager.delete(remove.project_id, confirm=True) is True
    assert not manager.exists(remove.project_id)
    assert manager.exists(keep.project_id)
    # source file is never touched
    assert (tmp_path / "keep.txt").exists()


def test_delete_missing_returns_false(tmp_path):
    manager = _manager(tmp_path)
    assert manager.delete("nope", confirm=True) is False


# -- storage ---------------------------------------------------------------

def test_resolve_ntpe_home_honors_env_override(tmp_path):
    resolved = resolve_ntpe_home({"NTPE_HOME": str(tmp_path / "custom")})
    assert resolved == (tmp_path / "custom").resolve()


def test_project_id_path_traversal_rejected(tmp_path):
    store = ProjectStore(home=tmp_path)
    for bad in ("../escape", "a/b", "a\\b", ".."):
        with pytest.raises(ValueError):
            store.project_dir(bad)


def test_atomic_write_leaves_no_temp_files(tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_txt(tmp_path))
    project_dir = manager.store.project_dir(project.project_id)
    leftovers = [p.name for p in project_dir.iterdir() if p.name.endswith(".tmp")]
    assert leftovers == []


def test_two_managers_same_home_share_projects(tmp_path):
    home = tmp_path / "NTPE_HOME"
    p1 = ReaderProjectManager(home=home).create(_txt(tmp_path), title="Shared")
    p2 = ReaderProjectManager(home=home).load(p1.project_id)
    assert p2.book.title == "Shared"
