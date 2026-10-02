"""S9-07 Failure / Recovery / Separation / Isolation / Persistence matrix.

Deterministic, offline, isolated. Fake runtime + fake opener.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.reader_project.manager import ReaderProjectManager
from core.reader_project.models import OutputRecord
from core.reader_project.recovery import check_recovery_eligibility
from ui.translation_studio.project_view_model import build_card_model
from ui.translation_studio.pages.project_page import ProjectPage

from tests.e2e.conftest import (
    FakeResultOpener,
    FakeTranslationRunner,
    build_txt_book_info,
    make_txt,
)

_RUNNER = "ui.translation_studio.pages.project_page.TranslationRunner"
_MSGBOX = "ui.translation_studio.pages.project_page.QMessageBox"


def _write_resume(out_dir: Path, stem: str, chunks: dict, *, input_path=None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{stem}_resume_state.json"
    payload: dict = {"chunks": chunks, "output_dir": str(out_dir)}
    if input_path is not None:
        payload["input"] = str(input_path)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _restart(home) -> ProjectPage:
    page = ProjectPage()
    page.set_project_manager(ReaderProjectManager(home=home))
    page.set_result_opener(FakeResultOpener())
    page.refresh_projects()
    return page


# ---------------------------------------------------------------------------
# Failure UX
# ---------------------------------------------------------------------------

def test_translation_failure_is_explicit_and_preserves_last_error(
    qapp, tmp_path, manager, opener, page
):
    source = make_txt(tmp_path)
    pid = page.add_project(name="Novel", source=str(source), book_info=build_txt_book_info(source))
    page.table.selectRow(0)

    with patch(_RUNNER, FakeTranslationRunner):
        page._on_translate()
    with patch(_MSGBOX):
        FakeTranslationRunner.last().fail("provider unavailable")

    stored = manager.load(pid)
    assert stored.state.last_error == "翻譯失敗"
    # not fake-completed
    assert stored.output.artifact_path in (None, "")
    assert build_card_model(stored).can_open_result is False


# ---------------------------------------------------------------------------
# Missing output (S9-05 preservation)
# ---------------------------------------------------------------------------

def test_missing_output_is_not_faked(qapp, tmp_path, manager, opener, page):
    source = make_txt(tmp_path)
    pid = page.add_project(name="Novel", source=str(source), book_info=build_txt_book_info(source))
    stored = manager.load(pid)
    artifact = tmp_path / "out" / "novel_zh.txt"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("成品", encoding="utf-8")
    stored.output = OutputRecord(output_dir=str(artifact.parent), artifact_path=str(artifact), artifact_kind="txt", available=True)
    manager.update(stored, output=stored.output)

    assert build_card_model(manager.load(pid)).can_open_result is True
    artifact.unlink()
    model = build_card_model(manager.load(pid))
    assert model.can_open_result is False
    assert model.output_note == "結果檔案不存在"


# ---------------------------------------------------------------------------
# Output / Runtime artifact separation (both directions)
# ---------------------------------------------------------------------------

def test_runtime_valid_output_missing_recovery_eligible_output_unavailable(
    qapp, tmp_path, manager, opener, page
):
    source = make_txt(tmp_path)
    pid = page.add_project(name="Novel", source=str(source), book_info=build_txt_book_info(source))
    stored = manager.load(pid)
    out_dir = manager.store.home / "output" / pid
    resume = _write_resume(out_dir, source.stem, {f"{i:06d}": {"status": "success"} for i in range(1, 4)}, input_path=source)
    stored.execution.resume_state_path = str(resume)
    stored.book.total_units = 10
    manager.update(stored, execution=stored.execution, book=stored.book)

    model = build_card_model(manager.load(pid))
    assert model.recovery_eligible is True       # runtime artifact valid
    assert model.can_open_result is False        # output missing → not offered


def test_output_exists_runtime_invalid_recovery_blocked(qapp, tmp_path, manager, opener, page):
    source = make_txt(tmp_path)
    pid = page.add_project(name="Novel", source=str(source), book_info=build_txt_book_info(source))
    stored = manager.load(pid)
    artifact = tmp_path / "out" / "novel_zh.txt"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("成品", encoding="utf-8")
    stored.output = OutputRecord(output_dir=str(artifact.parent), artifact_path=str(artifact), artifact_kind="txt", available=True)
    # runtime artifact reference is missing → recovery must be blocked
    stored.execution.resume_state_path = str(tmp_path / "missing_resume.json")
    manager.update(stored, output=stored.output, execution=stored.execution)

    model = build_card_model(manager.load(pid))
    # output remains available (S9-05 contract) ...
    assert model.can_open_result is True
    # ... but recovery is blocked and never faked
    assert model.recovery_eligible is False
    assert model.recovery_blocked_by == "artifact"


# ---------------------------------------------------------------------------
# Project isolation
# ---------------------------------------------------------------------------

def test_outputs_never_cross_wire_between_projects(qapp, tmp_path, manager, opener, page):
    s1 = make_txt(tmp_path, "a.txt")
    s2 = make_txt(tmp_path, "b.txt")
    p1 = page.add_project(name="A", source=str(s1), book_info=build_txt_book_info(s1, "A"))
    p2 = page.add_project(name="B", source=str(s2), book_info=build_txt_book_info(s2, "B"))

    for pid, title in ((p1, "A"), (p2, "B")):
        stored = manager.load(pid)
        artifact = tmp_path / title / f"{title}_zh.txt"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("x", encoding="utf-8")
        stored.output = OutputRecord(output_dir=str(artifact.parent), artifact_path=str(artifact), artifact_kind="txt", available=True)
        manager.update(stored, output=stored.output)

    page._on_open_result(p1)
    assert opener.opened == [str(tmp_path / "A" / "A_zh.txt")]
    assert str(tmp_path / "B" / "B_zh.txt") not in opener.opened


# ---------------------------------------------------------------------------
# Normal Translation vs Recovery
# ---------------------------------------------------------------------------

def test_normal_translation_allowed_while_recovery_blocked(qapp, tmp_path, manager, opener, page):
    source = make_txt(tmp_path)
    pid = page.add_project(name="Novel", source=str(source), book_info=build_txt_book_info(source))
    page.table.selectRow(0)

    blocked_by, _ = manager.get_recovery_blocked_reason(pid)
    assert blocked_by == "artifact"  # recovery blocked

    with patch(_RUNNER, FakeTranslationRunner):
        page._on_translate()          # normal translation still allowed
    assert FakeTranslationRunner.last() is not None


# ---------------------------------------------------------------------------
# Persistence across restart matrix
# ---------------------------------------------------------------------------

def test_import_then_restart_persists(qapp, tmp_path, manager, opener, page):
    source = make_txt(tmp_path)
    pid = page.add_project(name="Novel", source=str(source), book_info=build_txt_book_info(source))
    page2 = _restart(manager.store.home)
    try:
        assert page2._persisted_ids == [pid]
    finally:
        page2.close()


def test_translate_then_restart_before_completion_is_truthful(qapp, tmp_path, manager, opener, page):
    source = make_txt(tmp_path)
    pid = page.add_project(name="Novel", source=str(source), book_info=build_txt_book_info(source))
    page.table.selectRow(0)
    with patch(_RUNNER, FakeTranslationRunner):
        page._on_translate()
    # no completion; restart
    page2 = _restart(manager.store.home)
    try:
        model = build_card_model(ReaderProjectManager(home=manager.store.home).load(pid))
        assert model.reader_status != "completed"   # not faked complete
        assert model.can_open_result is False
    finally:
        page2.close()


def test_failed_then_restart_error_remains(qapp, tmp_path, manager, opener, page):
    source = make_txt(tmp_path)
    pid = page.add_project(name="Novel", source=str(source), book_info=build_txt_book_info(source))
    page.table.selectRow(0)
    with patch(_RUNNER, FakeTranslationRunner):
        page._on_translate()
    with patch(_MSGBOX):
        FakeTranslationRunner.last().fail("boom")

    page2 = _restart(manager.store.home)
    try:
        stored = ReaderProjectManager(home=manager.store.home).load(pid)
        assert stored.state.last_error == "翻譯失敗"
    finally:
        page2.close()


def test_source_changed_then_restart_still_blocked(qapp, tmp_path, manager, opener, page):
    source = make_txt(tmp_path)
    pid = page.add_project(name="Novel", source=str(source), book_info=build_txt_book_info(source))
    stored = manager.load(pid)
    out_dir = manager.store.home / "output" / pid
    resume = _write_resume(out_dir, source.stem, {f"{i:06d}": {"status": "success"} for i in range(1, 4)})
    stored.execution.resume_state_path = str(resume)
    manager.update(stored, execution=stored.execution)
    source.write_bytes(b"changed after import")

    page2 = _restart(manager.store.home)
    try:
        model = build_card_model(ReaderProjectManager(home=manager.store.home).load(pid))
        assert model.recovery_eligible is False
        assert model.recovery_blocked_by == "source"
    finally:
        page2.close()


def test_output_missing_then_restart_open_result_unavailable(qapp, tmp_path, manager, opener, page):
    source = make_txt(tmp_path)
    pid = page.add_project(name="Novel", source=str(source), book_info=build_txt_book_info(source))
    stored = manager.load(pid)
    artifact = tmp_path / "out" / "novel_zh.txt"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("x", encoding="utf-8")
    stored.output = OutputRecord(output_dir=str(artifact.parent), artifact_path=str(artifact), artifact_kind="txt", available=True)
    manager.update(stored, output=stored.output)
    artifact.unlink()

    page2 = _restart(manager.store.home)
    try:
        assert build_card_model(ReaderProjectManager(home=manager.store.home).load(pid)).can_open_result is False
    finally:
        page2.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
