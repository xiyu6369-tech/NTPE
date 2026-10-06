"""S12-02 Glossary backend tests.

Hermetic: tmp ``NTPE_HOME``; deterministic fixtures; no provider, no network, no
real translation. Exercises the project-scoped Glossary backend directly (no UI).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.reader_project import glossary as g
from core.reader_project.manager import ReaderProjectManager


def _manager(tmp_path: Path) -> ReaderProjectManager:
    return ReaderProjectManager(home=tmp_path / "NTPE_HOME")


def _source(tmp_path: Path) -> Path:
    path = tmp_path / "novel.txt"
    path.write_text("정태의는 일라이를 보았다.\n", encoding="utf-8")
    return path


def _text_glossary(tmp_path: Path, name: str = "glossary.txt") -> Path:
    path = tmp_path / name
    path.write_text("정태의=鄭泰義\n일라이 -> 伊萊\n카일 → 凱爾\n# comment\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# A — Import
# ---------------------------------------------------------------------------

def test_text_import_parses_all_delimiters(tmp_path):
    entries, fmt = g.parse_glossary_file(_text_glossary(tmp_path))
    assert fmt == g.FORMAT_TEXT
    assert entries == {"정태의": "鄭泰義", "일라이": "伊萊", "카일": "凱爾"}


def test_json_import_parses_pairs(tmp_path):
    path = tmp_path / "glossary.json"
    path.write_text(json.dumps({"정태의": "鄭泰義", "nested": {"일라이": "伊萊"}}), encoding="utf-8")
    entries, fmt = g.parse_glossary_file(path)
    assert fmt == g.FORMAT_JSON
    assert entries["정태의"] == "鄭泰義"
    assert entries["일라이"] == "伊萊"


def test_import_rejects_empty_and_whitespace(tmp_path):
    empty = tmp_path / "empty.txt"
    empty.write_text("\n# only comments\n   \n", encoding="utf-8")
    with pytest.raises(g.GlossaryValidationError):
        g.parse_glossary_file(empty)

    whitespace = tmp_path / "ws.txt"
    whitespace.write_text("   =   \n= X\nY =\n", encoding="utf-8")
    with pytest.raises(g.GlossaryValidationError):
        g.parse_glossary_file(whitespace)


def test_import_rejects_unsupported_format(tmp_path):
    path = tmp_path / "glossary.csv"
    path.write_text("a,b\n", encoding="utf-8")
    with pytest.raises(g.GlossaryValidationError):
        g.parse_glossary_file(path)


def test_import_rejects_oversized(tmp_path, monkeypatch):
    monkeypatch.setattr(g, "MAX_GLOSSARY_BYTES", 4)
    with pytest.raises(g.GlossaryValidationError):
        g.parse_glossary_file(_text_glossary(tmp_path))


def test_import_rejects_decode_failure(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_bytes(b"\xff\xfe\xfa\xfb=\x00")
    with pytest.raises(g.GlossaryValidationError):
        g.parse_glossary_file(path)


def test_import_rejects_missing_file(tmp_path):
    with pytest.raises(g.GlossaryValidationError):
        g.parse_glossary_file(tmp_path / "nope.txt")


# ---------------------------------------------------------------------------
# B — Identity
# ---------------------------------------------------------------------------

def test_same_normalized_content_same_hash(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("A=X\nB=Y\n", encoding="utf-8")
    b.write_text("B = Y\n\nA = X\n", encoding="utf-8")
    assert g.build_record_for_file(a).content_hash == g.build_record_for_file(b).content_hash


def test_changed_content_different_hash(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("A=X\n", encoding="utf-8")
    b.write_text("A=Z\n", encoding="utf-8")
    assert g.build_record_for_file(a).content_hash != g.build_record_for_file(b).content_hash


# ---------------------------------------------------------------------------
# C — Project attach / load / save / replace / detach
# ---------------------------------------------------------------------------

def test_create_without_glossary(tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), format="txt", title="T")
    assert project.glossary is None
    assert manager.load(project.project_id).glossary is None


def test_attach_persists_and_loads(tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), format="txt", title="T")
    attached = manager.attach_glossary(project, _text_glossary(tmp_path))

    assert attached.glossary is not None
    assert attached.glossary.mode == g.MODE_PROJECT_FILE
    assert attached.glossary.term_count == 3
    assert Path(attached.glossary.stored_path).is_file()

    reloaded = manager.load(project.project_id)
    assert reloaded.glossary is not None
    assert reloaded.glossary.content_hash == attached.glossary.content_hash
    assert manager.resolve_glossary(reloaded)["정태의"] == "鄭泰義"


def test_replace_updates_hash_and_removes_old_snapshot(tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), format="txt", title="T")
    project = manager.attach_glossary(project, _text_glossary(tmp_path))
    old_hash = project.glossary.content_hash
    old_path = Path(project.glossary.stored_path)

    new_gl = tmp_path / "gl2.txt"
    new_gl.write_text("정태의=鄭泰益\n", encoding="utf-8")
    project = manager.replace_glossary(project, new_gl)

    assert project.glossary.content_hash != old_hash
    assert Path(project.glossary.stored_path).is_file()
    assert not old_path.exists()
    assert manager.resolve_glossary(manager.load(project.project_id)) == {"정태의": "鄭泰益"}


def test_detach_clears_and_keeps_project(tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), format="txt", title="T")
    project = manager.attach_glossary(project, _text_glossary(tmp_path))
    snapshot = Path(project.glossary.stored_path)

    project = manager.detach_glossary(project)
    assert project.glossary is None
    assert not snapshot.exists()
    assert manager.resolve_glossary(manager.load(project.project_id)) == {}
    # Unrelated state intact
    assert manager.load(project.project_id).source.path == str(_source(tmp_path))


# ---------------------------------------------------------------------------
# D — Persistence (original external file disappearance)
# ---------------------------------------------------------------------------

def test_original_file_missing_still_resolves(tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), format="txt", title="T")
    gl = _text_glossary(tmp_path)
    project = manager.attach_glossary(project, gl)
    gl.unlink()

    reloaded = manager.load(project.project_id)
    assert manager.resolve_glossary(reloaded)["카일"] == "凱爾"


# ---------------------------------------------------------------------------
# Corrupt / missing snapshot
# ---------------------------------------------------------------------------

def test_missing_snapshot_raises_integrity(tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), format="txt", title="T")
    project = manager.attach_glossary(project, _text_glossary(tmp_path))
    Path(project.glossary.stored_path).unlink()

    with pytest.raises(g.GlossaryIntegrityError):
        manager.resolve_glossary(manager.load(project.project_id))


def test_corrupt_snapshot_raises_integrity(tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), format="txt", title="T")
    project = manager.attach_glossary(project, _text_glossary(tmp_path))
    Path(project.glossary.stored_path).write_text('{"tampered": "值"}', encoding="utf-8")

    with pytest.raises(g.GlossaryIntegrityError):
        manager.resolve_glossary(manager.load(project.project_id))


# ---------------------------------------------------------------------------
# I — Conflict semantics
# ---------------------------------------------------------------------------

def test_within_file_last_wins(tmp_path):
    path = tmp_path / "dup.txt"
    path.write_text("A=X\nA=Y\n", encoding="utf-8")
    entries, _ = g.parse_glossary_file(path)
    assert entries == {"A": "Y"}


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

def test_store_rejects_non_hex_content_hash(tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), format="txt", title="T")
    with pytest.raises(ValueError):
        manager.store.glossary_snapshot_path(project.project_id, "../../escape")
