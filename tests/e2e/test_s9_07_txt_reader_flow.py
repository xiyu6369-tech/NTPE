"""S9-07 TXT Reader-First E2E flow (TXT-01 .. TXT-12).

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


def _write_resume(out_dir: Path, stem: str, chunks: dict) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{stem}_resume_state.json"
    path.write_text(json.dumps({"chunks": chunks}), encoding="utf-8")
    return path


def _success_result(artifact: Path, out_dir: Path, total: int = 2) -> dict:
    return {
        "status": "success",
        "output": str(artifact),
        "output_dir": str(out_dir),
        "chunk_total": total,
        "chunk_successful": total,
        "chunk_failed": 0,
        "session_id": "s9-07",
    }


# ---------------------------------------------------------------------------
# TXT-01..TXT-03 — Import / Project / Persistence
# ---------------------------------------------------------------------------

def test_txt_import_creates_persistent_project(qapp, tmp_path, manager, opener, page):
    source = make_txt(tmp_path)
    pid = page.add_project(
        name="雙月之夜",
        source=str(source),
        status="已匯入",
        progress="0%",
        book_info=build_txt_book_info(source, "雙月之夜"),
    )
    assert pid is not None
    assert manager.exists(pid)

    stored = manager.load(pid)
    assert stored.source.hash  # canonical source identity recorded
    assert stored.source.format == "txt"
    assert stored.book.title == "雙月之夜"
    assert page.table.rowCount() == 1
    assert page._persisted_ids[0] == pid


def test_txt_import_failure_does_not_persist(qapp, tmp_path, manager, page):
    # non-existent source path → no persistent project, honest in-memory row
    page.add_project(name="Missing", source=str(tmp_path / "nope.txt"), status="已匯入")
    assert page._persisted_ids[0] is None
    assert manager.list_projects() == []


def test_txt_project_persists_across_restart(qapp, tmp_path, manager, opener, page):
    source = make_txt(tmp_path)
    pid = page.add_project(
        name="Novel", source=str(source), book_info=build_txt_book_info(source, "Novel")
    )
    before = manager.load(pid)

    # "restart": new manager + new page on the same home
    manager2 = ReaderProjectManager(home=manager.store.home)
    page2 = ProjectPage()
    try:
        page2.set_project_manager(manager2)
        page2.refresh_projects()
        assert page2.table.rowCount() == 1
        assert page2._persisted_ids[0] == pid
        after = manager2.load(pid)
        assert after.source.hash == before.source.hash
        assert after.source.path == before.source.path
    finally:
        page2.close()


# ---------------------------------------------------------------------------
# TXT-04..TXT-09 — Translation / Progress / Completion / Output / Open Result
# ---------------------------------------------------------------------------

def test_txt_normal_translation_without_recovery_artifact(qapp, tmp_path, manager, opener, page):
    """A new project (no runtime artifact) must still start normal translation."""
    source = make_txt(tmp_path)
    pid = page.add_project(name="Novel", source=str(source), book_info=build_txt_book_info(source))
    page.table.selectRow(0)

    # recovery is blocked (no artifact)...
    blocked_by, _ = manager.get_recovery_blocked_reason(pid)
    assert blocked_by == "artifact"

    # ...but normal translation is allowed (S9-06 Repair invariant)
    with patch(_RUNNER, FakeTranslationRunner):
        page._on_translate()
    runner = FakeTranslationRunner.last()
    assert runner is not None and runner.started
    assert runner.options.resume is True


def test_txt_full_journey_progress_completion_output_open_result(
    qapp, tmp_path, manager, opener, page
):
    source = make_txt(tmp_path)
    pid = page.add_project(name="Novel", source=str(source), book_info=build_txt_book_info(source))
    page.table.selectRow(0)

    with patch(_RUNNER, FakeTranslationRunner):
        page._on_translate()
    runner = FakeTranslationRunner.last()

    # progress observable, not fake-completed while unfinished
    runner.emit_progress({"status": "running", "chunk_total": 10, "chunk_completed": 3, "message": ""})
    assert "3" in page.table.item(0, 3).text()

    # deterministic artifact + resume state (as runtime would write)
    out_dir = Path(runner.options.output_dir)
    artifact = out_dir / f"{source.stem}_zh.txt"
    artifact.write_text("成品", encoding="utf-8")
    _write_resume(out_dir, source.stem, {f"{i:06d}": {"status": "success"} for i in range(1, 3)})

    with patch(_MSGBOX):
        runner.complete(_success_result(artifact, out_dir))

    stored = manager.load(pid)
    assert stored.output.artifact_path == str(artifact)
    assert stored.output.available is True
    assert Path(stored.output.artifact_path).is_absolute()

    # completion presentation
    model = build_card_model(manager.load(pid))
    assert model.reader_status == "completed"
    assert model.can_open_result is True

    # open result uses the exact project artifact; no OS launch
    page._on_open_result(pid)
    assert opener.opened == [str(artifact)]


def test_txt_output_is_project_owned_and_isolated(qapp, tmp_path, manager, page):
    s1 = make_txt(tmp_path, "a.txt")
    s2 = make_txt(tmp_path, "b.txt")
    p1 = page.add_project(name="A", source=str(s1), book_info=build_txt_book_info(s1, "A"))
    p2 = page.add_project(name="B", source=str(s2), book_info=build_txt_book_info(s2, "B"))

    page.table.selectRow(page._row_for_project_id(p1))
    with patch(_RUNNER, FakeTranslationRunner):
        page._on_translate()
    out1 = Path(FakeTranslationRunner.last().options.output_dir)

    FakeTranslationRunner.reset()
    page.table.selectRow(page._row_for_project_id(p2))
    with patch(_RUNNER, FakeTranslationRunner):
        page._on_translate()
    out2 = Path(FakeTranslationRunner.last().options.output_dir)

    assert out1 != out2
    assert out1.is_absolute() and out2.is_absolute()
    assert manager.store.home in out1.parents or manager.store.home in out2.parents


def test_txt_completion_survives_restart_and_open_result_meaningful(
    qapp, tmp_path, manager, opener, page
):
    source = make_txt(tmp_path)
    pid = page.add_project(name="Novel", source=str(source), book_info=build_txt_book_info(source))
    page.table.selectRow(0)
    with patch(_RUNNER, FakeTranslationRunner):
        page._on_translate()
    runner = FakeTranslationRunner.last()
    out_dir = Path(runner.options.output_dir)
    artifact = out_dir / f"{source.stem}_zh.txt"
    artifact.write_text("成品", encoding="utf-8")
    _write_resume(out_dir, source.stem, {f"{i:06d}": {"status": "success"} for i in range(1, 3)})
    with patch(_MSGBOX):
        runner.complete(_success_result(artifact, out_dir))

    # restart
    manager2 = ReaderProjectManager(home=manager.store.home)
    opener2 = FakeResultOpener()
    page2 = ProjectPage()
    try:
        page2.set_project_manager(manager2)
        page2.set_result_opener(opener2)
        page2.refresh_projects()
        model = build_card_model(manager2.load(pid))
        assert model.reader_status == "completed"
        assert model.can_open_result is True
        page2._on_open_result(pid)
        assert opener2.opened == [str(artifact)]
    finally:
        page2.close()


# ---------------------------------------------------------------------------
# TXT-10..TXT-12 — Recovery / Source Changed / Source Missing
# ---------------------------------------------------------------------------

def test_txt_recovery_routes_to_existing_resume(qapp, tmp_path, manager, opener, page):
    source = make_txt(tmp_path)
    pid = page.add_project(name="Novel", source=str(source), book_info=build_txt_book_info(source))
    stored = manager.load(pid)
    out_dir = manager.store.home / "output" / pid
    resume = _write_resume(
        out_dir, source.stem,
        {**{f"{i:06d}": {"status": "success"} for i in range(1, 4)}, "000004": {"status": "failed"}},
    )
    stored.execution.resume_state_path = str(resume)
    stored.book.total_units = 10
    manager.update(stored, execution=stored.execution, book=stored.book)

    page.refresh_projects()
    model = build_card_model(manager.load(pid))
    assert model.reader_status == "resumable"
    assert model.recovery_eligible is True

    FakeTranslationRunner.reset()
    page.table.selectRow(0)
    with patch(_RUNNER, FakeTranslationRunner):
        page._on_resume(pid)
    runner = FakeTranslationRunner.last()
    assert runner is not None and runner.started
    assert runner.options.resume is True
    assert Path(runner.options.output_dir) == out_dir


def test_txt_source_changed_blocks_recovery(qapp, tmp_path, manager, opener, page):
    source = make_txt(tmp_path)
    pid = page.add_project(name="Novel", source=str(source), book_info=build_txt_book_info(source))
    stored = manager.load(pid)
    out_dir = manager.store.home / "output" / pid
    resume = _write_resume(out_dir, source.stem, {f"{i:06d}": {"status": "success"} for i in range(1, 4)})
    stored.execution.resume_state_path = str(resume)
    manager.update(stored, execution=stored.execution)
    page.refresh_projects()
    assert build_card_model(manager.load(pid)).recovery_eligible is True

    # change source content
    source.write_bytes(b"a completely different source")
    page.refresh_projects()
    model = build_card_model(manager.load(pid))
    assert model.recovery_eligible is False
    assert model.recovery_blocked_by == "source"

    # recovery action does not start a runner
    FakeTranslationRunner.reset()
    page.table.selectRow(0)
    with patch(_MSGBOX), patch(_RUNNER, FakeTranslationRunner):
        page._on_resume(pid)
    assert FakeTranslationRunner.last() is None


def test_txt_source_missing_blocks_recovery(qapp, tmp_path, manager, opener, page):
    source = make_txt(tmp_path)
    pid = page.add_project(name="Novel", source=str(source), book_info=build_txt_book_info(source))
    stored = manager.load(pid)
    out_dir = manager.store.home / "output" / pid
    resume = _write_resume(out_dir, source.stem, {f"{i:06d}": {"status": "success"} for i in range(1, 4)})
    stored.execution.resume_state_path = str(resume)
    manager.update(stored, execution=stored.execution)
    page.refresh_projects()
    assert build_card_model(manager.load(pid)).recovery_eligible is True

    source.unlink()
    page.refresh_projects()
    model = build_card_model(manager.load(pid))
    assert model.recovery_eligible is False
    assert model.recovery_blocked_by == "source"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
