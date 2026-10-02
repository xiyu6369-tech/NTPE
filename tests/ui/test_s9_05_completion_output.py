"""S9-05 Completion & Output UX tests.

Hermetic: tmp ``NTPE_HOME``; fake ``ResultOpener`` (no real OS launch);
no provider, no network, no real translation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.reader_project.manager import ReaderProjectManager
from core.reader_project.models import BookRecord, OutputRecord, StateRecord
from ui.translation_studio.pages.project_page import ProjectPage
from ui.translation_studio.project_view_model import build_card_model


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication(sys.argv)


class FakeResultOpener:
    """Records calls; never touches the OS."""

    def __init__(self, open_ok: bool = True, reveal_ok: bool = True):
        self.open_ok = open_ok
        self.reveal_ok = reveal_ok
        self.opened: list[str] = []
        self.revealed: list[str] = []

    def open_path(self, path) -> bool:
        self.opened.append(str(path))
        return self.open_ok

    def reveal_folder(self, path) -> bool:
        self.revealed.append(str(path))
        return self.reveal_ok


def _manager(tmp_path: Path) -> ReaderProjectManager:
    return ReaderProjectManager(home=tmp_path / "NTPE_HOME")


def _source(tmp_path: Path, name: str = "novel.txt", body: bytes = b"source") -> Path:
    path = tmp_path / name
    path.write_bytes(body)
    return path


def _page(manager, opener=None) -> ProjectPage:
    page = ProjectPage()
    page.set_project_manager(manager)
    if opener is not None:
        page.set_result_opener(opener)
    page.refresh_projects()
    return page


def _complete(manager, tmp_path, title="Novel", subdir="out"):
    project = manager.create(_source(tmp_path, f"{title}.txt", title.encode()), title=title)
    artifact = tmp_path / subdir / f"{title}_zh.txt"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("成品", encoding="utf-8")
    project.output = OutputRecord(
        output_dir=str(artifact.parent),
        artifact_path=str(artifact),
        artifact_kind="txt",
        available=True,
    )
    manager.update(project, output=project.output)
    return manager.load(project.project_id), artifact


# ---------------------------------------------------------------------------
# Completion state
# ---------------------------------------------------------------------------

def test_not_started_has_no_output_action(qapp, tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), title="Novel")
    model = build_card_model(manager.load(project.project_id))
    assert model.reader_status == "not_started"
    assert model.action_label == "開始翻譯"
    assert model.can_open_result is False
    assert model.output_reference_present is False


def test_in_progress_has_no_output_action(qapp, tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), title="Novel")
    resume = tmp_path / "novel_resume_state.json"
    resume.write_text(
        json.dumps({"chunks": {f"{i:06d}": {"status": "success"} for i in range(1, 3)}}),
        encoding="utf-8",
    )
    project.execution.resume_state_path = str(resume)
    project.book = BookRecord(format="txt", title="Novel", total_units=10)
    manager.update(project, execution=project.execution, book=project.book)

    model = build_card_model(manager.load(project.project_id))
    assert model.reader_status == "resumable"
    assert model.action_label == "繼續翻譯"
    assert model.can_open_result is False


def test_completed_with_output_exposes_result(qapp, tmp_path):
    manager = _manager(tmp_path)
    project, artifact = _complete(manager, tmp_path, title="Novel")
    model = build_card_model(manager.load(project.project_id))
    assert model.reader_status == "completed"
    assert model.output_exists is True
    assert model.can_open_result is True
    assert model.can_reveal_folder is True
    assert model.output_name == "Novel_zh.txt"
    assert model.output_kind_label == "TXT"
    assert model.action_label == ""  # no resume on a completed project


def test_completed_missing_output_is_not_faked(qapp, tmp_path):
    manager = _manager(tmp_path)
    project, artifact = _complete(manager, tmp_path, title="Novel")
    artifact.unlink()

    model = build_card_model(manager.load(project.project_id))
    assert model.reader_status != "completed"  # canonical derivation demotes it
    assert model.can_open_result is False
    assert model.output_note == "結果檔案不存在"


def test_hard_failure_keeps_canonical_status_and_note(qapp, tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), title="Novel")
    project.state = StateRecord(reader_status="failed", last_error="翻譯失敗")
    manager.update(project, state=project.state)

    model = build_card_model(manager.load(project.project_id))
    assert model.note == "翻譯失敗"
    assert model.can_open_result is False


# ---------------------------------------------------------------------------
# Open Result
# ---------------------------------------------------------------------------

def test_open_result_uses_correct_absolute_project_output(qapp, tmp_path):
    manager = _manager(tmp_path)
    project, artifact = _complete(manager, tmp_path, title="Novel")
    opener = FakeResultOpener()
    page = _page(manager, opener)
    try:
        with patch("ui.translation_studio.pages.project_page.QMessageBox") as msg:
            page._on_open_result(project.project_id)
        assert opener.opened == [str(artifact)]
        assert Path(opener.opened[0]).is_absolute()
        assert not msg.warning.called
    finally:
        page.close()


def test_open_result_missing_does_not_call_opener_or_mutate(qapp, tmp_path):
    manager = _manager(tmp_path)
    project, artifact = _complete(manager, tmp_path, title="Novel")
    artifact.unlink()
    before = manager.store.project_file(project.project_id).read_text(encoding="utf-8")

    opener = FakeResultOpener()
    page = _page(manager, opener)
    try:
        with patch("ui.translation_studio.pages.project_page.QMessageBox") as msg:
            page._on_open_result(project.project_id)
        assert opener.opened == []
        assert msg.information.called
        assert not msg.warning.called
    finally:
        page.close()

    after = manager.store.project_file(project.project_id).read_text(encoding="utf-8")
    assert before == after  # no state mutation


def test_open_failure_does_not_modify_project_state(qapp, tmp_path):
    manager = _manager(tmp_path)
    project, artifact = _complete(manager, tmp_path, title="Novel")
    before = manager.store.project_file(project.project_id).read_text(encoding="utf-8")

    opener = FakeResultOpener(open_ok=False)
    page = _page(manager, opener)
    try:
        with patch("ui.translation_studio.pages.project_page.QMessageBox") as msg:
            page._on_open_result(project.project_id)
        assert opener.opened == [str(artifact)]
        assert msg.warning.called
    finally:
        page.close()

    after = manager.store.project_file(project.project_id).read_text(encoding="utf-8")
    assert before == after


def test_reveal_folder_uses_project_output(qapp, tmp_path):
    manager = _manager(tmp_path)
    project, artifact = _complete(manager, tmp_path, title="Novel")
    opener = FakeResultOpener()
    page = _page(manager, opener)
    try:
        with patch("ui.translation_studio.pages.project_page.QMessageBox"):
            page._on_reveal_folder(project.project_id)
        assert opener.revealed == [str(artifact)]
    finally:
        page.close()


def test_card_open_signal_routes_to_open_result(qapp, tmp_path):
    manager = _manager(tmp_path)
    project, artifact = _complete(manager, tmp_path, title="Novel")
    opener = FakeResultOpener()
    page = _page(manager, opener)
    try:
        card = page._cards[project.project_id]
        assert card is not None
        with patch("ui.translation_studio.pages.project_page.QMessageBox"):
            card.open_result_requested.emit(project.project_id)
        assert opener.opened == [str(artifact)]
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Isolation
# ---------------------------------------------------------------------------

def test_outputs_are_never_cross_wired(qapp, tmp_path):
    manager = _manager(tmp_path)
    pa, art_a = _complete(manager, tmp_path, title="Alpha", subdir="out_a")
    pb, art_b = _complete(manager, tmp_path, title="Beta", subdir="out_b")

    opener = FakeResultOpener()
    page = _page(manager, opener)
    try:
        with patch("ui.translation_studio.pages.project_page.QMessageBox"):
            page._on_open_result(pa.project_id)
        assert opener.opened == [str(art_a)]
        assert str(art_b) not in opener.opened
    finally:
        page.close()


def test_same_filename_distinct_projects_open_their_own_output(qapp, tmp_path):
    manager = _manager(tmp_path)
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    sa = dir_a / "novel.txt"
    sb = dir_b / "novel.txt"
    sa.write_bytes(b"A")
    sb.write_bytes(b"B")
    pa = manager.create(sa, title="Novel")
    pb = manager.create(sb, title="Novel")

    art_a = dir_a / "novel_zh.txt"
    art_b = dir_b / "novel_zh.txt"
    art_a.write_text("A", encoding="utf-8")
    art_b.write_text("B", encoding="utf-8")
    for p, art in ((pa, art_a), (pb, art_b)):
        p.output = OutputRecord(artifact_path=str(art), artifact_kind="txt", available=True)
        manager.update(p, output=p.output)

    opener = FakeResultOpener()
    page = _page(manager, opener)
    try:
        with patch("ui.translation_studio.pages.project_page.QMessageBox"):
            page._on_open_result(pa.project_id)
        assert opener.opened == [str(art_a)]
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_completion_output_survives_reload(qapp, tmp_path):
    manager = _manager(tmp_path)
    project, artifact = _complete(manager, tmp_path, title="Novel")

    reopened = ReaderProjectManager(home=manager.store.home)
    reloaded = reopened.load(project.project_id)
    model = build_card_model(reloaded)
    assert model.reader_status == "completed"
    assert model.can_open_result is True
    assert model.output_name == "Novel_zh.txt"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
