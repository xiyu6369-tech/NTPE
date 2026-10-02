"""S9-04 Reader Progress Dashboard / Project Card Library tests.

Hermetic: tmp ``NTPE_HOME`` injected manager; fake runner; no provider, no
network, no real translation, no real user storage.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.reader_project.manager import ReaderProjectManager
from ui.translation_studio.pages.project_page import ProjectPage
from ui.translation_studio.project_view_model import build_card_model


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication(sys.argv)


def _manager(tmp_path: Path) -> ReaderProjectManager:
    return ReaderProjectManager(home=tmp_path / "NTPE_HOME")


def _source(tmp_path: Path, name: str = "novel.txt", body: bytes = b"source") -> Path:
    path = tmp_path / name
    path.write_bytes(body)
    return path


def _page_with(manager: ReaderProjectManager) -> ProjectPage:
    page = ProjectPage()
    page.set_project_manager(manager)
    page.refresh_projects()
    return page


# ---------------------------------------------------------------------------
# Project library
# ---------------------------------------------------------------------------

def test_empty_library_shows_empty_state(qapp, tmp_path):
    page = _page_with(_manager(tmp_path))
    try:
        assert page.table.rowCount() == 0
        assert not page.empty_label.isHidden()
        assert page.card_scroll.isHidden()
    finally:
        page.close()


def test_one_and_multiple_projects_render_cards(qapp, tmp_path):
    manager = _manager(tmp_path)
    manager.create(_source(tmp_path, "a.txt", b"aaa"), title="A")
    manager.create(_source(tmp_path, "b.txt", b"bbb"), title="B")

    page = _page_with(manager)
    try:
        assert page.table.rowCount() == 2
        assert len(page._cards) == 2
        assert page.empty_label.isHidden()
        assert not page.card_scroll.isHidden()
    finally:
        page.close()


def test_refresh_does_not_duplicate_cards(qapp, tmp_path):
    manager = _manager(tmp_path)
    manager.create(_source(tmp_path), title="A")
    page = _page_with(manager)
    try:
        page.refresh_projects()
        page.refresh_projects()
        assert page.table.rowCount() == 1
        assert len(page._cards) == 1
    finally:
        page.close()


def test_refresh_skips_corrupt_project_without_crashing(qapp, tmp_path):
    manager = _manager(tmp_path)
    good = manager.create(_source(tmp_path, "good.txt"), title="Good")
    bad = manager.store.projects_root / "corrupt"
    bad.mkdir(parents=True)
    (bad / "project.json").write_text("{broken", encoding="utf-8")

    page = _page_with(manager)
    try:
        assert page.table.rowCount() == 1
        assert page._persisted_ids == [good.project_id]
    finally:
        page.close()


def test_list_failure_does_not_crash(qapp, tmp_path):
    class _Boom:
        store = None

        def list_projects(self):
            raise RuntimeError("boom")

    page = ProjectPage()
    try:
        page.set_project_manager(_Boom())  # type: ignore[arg-type]
        page.refresh_projects()  # must not raise
        assert page.table.rowCount() == 0
    finally:
        page.close()


# ---------------------------------------------------------------------------
# New Project
# ---------------------------------------------------------------------------

def test_new_project_creates_persistent_project(qapp, tmp_path):
    manager = _manager(tmp_path)
    source = _source(tmp_path, "newbook.txt")

    page = ProjectPage()
    try:
        page.set_project_manager(manager)
        with patch(
            "ui.translation_studio.pages.project_page.QFileDialog.getOpenFileName",
            return_value=(str(source), ""),
        ):
            project_id = page.new_project()

        assert project_id is not None
        assert manager.exists(project_id)
        assert len(manager.list_projects()) == 1
        assert page.table.rowCount() == 1
        assert page._persisted_ids == [project_id]
        # reloadable from storage
        assert manager.load(project_id).book.title == "newbook"
    finally:
        page.close()


def test_new_project_cancel_creates_nothing(qapp, tmp_path):
    manager = _manager(tmp_path)
    page = ProjectPage()
    try:
        page.set_project_manager(manager)
        with patch(
            "ui.translation_studio.pages.project_page.QFileDialog.getOpenFileName",
            return_value=("", ""),
        ):
            assert page.new_project() is None
        assert manager.list_projects() == []
        assert page.table.rowCount() == 0
    finally:
        page.close()


def test_new_project_without_manager_does_not_fake_success(qapp):
    page = ProjectPage()
    try:
        with patch("ui.translation_studio.pages.project_page.QFileDialog.getOpenFileName") as dlg, \
                patch("ui.translation_studio.pages.project_page.QMessageBox") as msg:
            assert page.new_project() is None
            assert not dlg.called
            assert msg.warning.called
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Open / Resume
# ---------------------------------------------------------------------------

def test_card_action_routes_resume_through_canonical_project(qapp, tmp_path):
    manager = _manager(tmp_path)
    source = _source(tmp_path)
    project = manager.create(source, title="Novel")

    page = _page_with(manager)
    try:
        page.table.selectRow(0)
        captured: dict = {}

        def _fake_runner(options, root_path):
            captured["options"] = options
            return MagicMock()

        with patch(
            "ui.translation_studio.pages.project_page.TranslationRunner",
            side_effect=_fake_runner,
        ):
            # emit the card's real action signal
            page._cards[project.project_id].action_requested.emit(project.project_id)

        assert captured["options"].resume is True
        assert captured["options"].output_dir == manager.store.home / "output" / project.project_id
    finally:
        page.close()


def test_resume_labels_use_canonical_contract(qapp, tmp_path):
    manager = _manager(tmp_path)
    source = _source(tmp_path)
    project = manager.create(source, title="Novel")

    # canonical labels (S9-03)
    page = _page_with(manager)
    try:
        assert page.table.item(0, 2).text() == "未開始"
    finally:
        page.close()

    # partial resume state → resumable
    resume = tmp_path / "novel_resume_state.json"
    resume.write_text(
        json.dumps({"chunks": {f"{i:06d}": {"status": "success"} for i in range(1, 3)}}),
        encoding="utf-8",
    )
    project = manager.load(project.project_id)
    project.execution.resume_state_path = str(resume)
    project.book.total_units = 10
    manager.update(project, execution=project.execution, book=project.book)

    page = _page_with(manager)
    try:
        assert page.table.item(0, 2).text() == "可繼續翻譯"
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Source identity / missing source
# ---------------------------------------------------------------------------

def test_same_filename_distinct_identity_stays_distinct(qapp, tmp_path):
    manager = _manager(tmp_path)
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    sa = dir_a / "novel.txt"
    sb = dir_b / "novel.txt"
    sa.write_bytes(b"version A")
    sb.write_bytes(b"version B")

    pa = manager.create(sa, title="Novel")
    pb = manager.create(sb, title="Novel")

    page = _page_with(manager)
    try:
        assert pa.project_id != pb.project_id
        assert page.table.rowCount() == 2
        assert set(page._persisted_ids) == {pa.project_id, pb.project_id}
    finally:
        page.close()


def test_missing_source_card_has_no_action(qapp, tmp_path):
    manager = _manager(tmp_path)
    source = _source(tmp_path)
    project = manager.create(source, title="Novel")
    source.unlink()

    page = _page_with(manager)
    try:
        model = build_card_model(manager.load(project.project_id))
        assert model.source_exists is False
        assert model.can_act is False
        assert model.action_label == ""
        card = page._cards[project.project_id]
        assert card is not None
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def test_delete_requires_confirmation_and_is_scoped(qapp, tmp_path):
    manager = _manager(tmp_path)
    keep = manager.create(_source(tmp_path, "keep.txt", b"keep"), title="Keep")
    remove = manager.create(_source(tmp_path, "remove.txt", b"remove"), title="Remove")

    page = _page_with(manager)
    try:
        # decline → nothing deleted
        with patch(
            "ui.translation_studio.pages.project_page.QMessageBox.question",
            return_value=__import__("PySide6.QtWidgets", fromlist=["QMessageBox"]).QMessageBox.StandardButton.No,
        ):
            page._on_delete_project(remove.project_id)
        assert manager.exists(remove.project_id)
        assert page.table.rowCount() == 2

        # confirm → only the targeted project is removed
        with patch(
            "ui.translation_studio.pages.project_page.QMessageBox.question",
            return_value=__import__("PySide6.QtWidgets", fromlist=["QMessageBox"]).QMessageBox.StandardButton.Yes,
        ):
            page._on_delete_project(remove.project_id)

        assert not manager.exists(remove.project_id)
        assert manager.exists(keep.project_id)
        assert page.table.rowCount() == 1
        assert page._persisted_ids == [keep.project_id]
        # unrelated source file untouched
        assert (tmp_path / "keep.txt").exists()
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Injection
# ---------------------------------------------------------------------------

def test_dashboard_never_touches_real_home(qapp, tmp_path, monkeypatch):
    """No default manager is created unless injected (MainWindow owns startup)."""
    monkeypatch.setenv("NTPE_HOME", str(tmp_path / "should-not-be-used"))
    page = ProjectPage()
    try:
        page.add_project(name="x", source="input/none.txt")
        assert page._persisted_ids == [None]
        assert not (tmp_path / "should-not-be-used").exists()
    finally:
        page.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
