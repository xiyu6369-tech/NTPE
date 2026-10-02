"""S9-03 Resume / Reader-Library UX tests.

Hermetic: tmp ``NTPE_HOME``; fake runner; no provider, no network, no real
translation.
"""

from __future__ import annotations

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


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication(sys.argv)


def _manager(tmp_path: Path) -> ReaderProjectManager:
    return ReaderProjectManager(home=tmp_path / "NTPE_HOME")


def _real_source(tmp_path: Path) -> Path:
    path = tmp_path / "novel.txt"
    path.write_bytes("그는 문을 열었다.\n".encode("utf-8"))
    return path


def test_refresh_projects_renders_persisted_project(qapp, tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_real_source(tmp_path), title="雙月之夜")

    page = ProjectPage()
    try:
        page.set_project_manager(manager)
        page.refresh_projects()
        assert page.table.rowCount() == 1
        assert page.table.item(0, 0).text() == "雙月之夜"
        assert page.table.item(0, 2).text() == "未開始"
        assert page.table.item(0, 3).text() == "0%"
        assert page._persisted_ids[0] == project.project_id
    finally:
        page.close()


def test_add_project_persists_real_source(qapp, tmp_path):
    manager = _manager(tmp_path)
    page = ProjectPage()
    try:
        page.set_project_manager(manager)
        page.add_project(
            name="新小說",
            source=str(_real_source(tmp_path)),
            status="已匯入",
            progress="0%",
            book_info={"title": "新小說", "source": str(tmp_path / "novel.txt")},
        )
        project_id = page._persisted_ids[0]
        assert project_id is not None
        assert manager.exists(project_id)
        # reader-facing status wins over the import status
        assert page.table.item(0, 2).text() == "未開始"
    finally:
        page.close()


def test_add_project_without_source_is_not_persisted(qapp, tmp_path):
    manager = _manager(tmp_path)
    page = ProjectPage()
    try:
        page.set_project_manager(manager)
        page.add_project(
            name="Test Novel",
            source="input/does-not-exist.txt",
            status="已匯入",
            progress="0%",
            book_info={"title": "Test Novel", "source": "input/does-not-exist.txt"},
        )
        assert page._persisted_ids[0] is None
        assert page.table.item(0, 2).text() == "已匯入"
        assert manager.list_projects() == []
    finally:
        page.close()


def test_no_manager_keeps_legacy_in_memory_behavior(qapp):
    page = ProjectPage()
    try:
        page.add_project(
            name="Legacy",
            source="input/test.txt",
            status="已匯入",
            progress="0%",
            book_info={"source": "input/test.txt"},
        )
        assert page._persisted_ids == [None]
        assert page.table.rowCount() == 1
    finally:
        page.close()


def test_isolation_between_managers(qapp, tmp_path):
    home_a = tmp_path / "A"
    home_b = tmp_path / "B"
    ReaderProjectManager(home=home_a).create(_real_source(tmp_path), title="A-book")

    page = ProjectPage()
    try:
        page.set_project_manager(ReaderProjectManager(home=home_b))
        page.refresh_projects()
        assert page.table.rowCount() == 0

        page.set_project_manager(ReaderProjectManager(home=home_a))
        page.refresh_projects()
        assert page.table.rowCount() == 1
    finally:
        page.close()


def test_persisted_txt_output_dir_is_absolute_and_stable(qapp, tmp_path):
    manager = _manager(tmp_path)
    source = _real_source(tmp_path)
    project = manager.create(source, title="Novel")

    page = ProjectPage()
    try:
        page.set_project_manager(manager)
        page.refresh_projects()
        page.table.selectRow(0)

        captured: dict = {}

        def _fake_runner(options, root_path):
            captured["options"] = options
            return MagicMock()

        with patch(
            "ui.translation_studio.pages.project_page.TranslationRunner",
            side_effect=_fake_runner,
        ):
            page._on_translate()

        expected = manager.store.home / "output" / project.project_id
        assert captured["options"].output_dir == expected
        assert captured["options"].output_dir.is_absolute()
    finally:
        page.close()


def test_translation_finished_persists_runtime_artifact_reference(qapp, tmp_path):
    manager = _manager(tmp_path)
    source = _real_source(tmp_path)
    project = manager.create(source, title="Novel")

    artifact_dir = tmp_path / "out"
    artifact = artifact_dir / "novel_zh.txt"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("成品", encoding="utf-8")

    page = ProjectPage()
    try:
        page.set_project_manager(manager)
        page.refresh_projects()
        page._current_translation_row = 0
        page._translation_runner = MagicMock()

        result = {
            "status": "success",
            "output": str(artifact),
            "output_dir": str(artifact_dir),
            "chunk_total": 1,
            "chunk_successful": 1,
            "chunk_failed": 0,
            "session_id": "s1",
        }
        with patch("ui.translation_studio.pages.project_page.QMessageBox"):
            page._on_translation_finished(result)

        reloaded = manager.load(project.project_id)
        assert reloaded.output.artifact_path == str(artifact)
        assert reloaded.output.available is True
        assert reloaded.output.artifact_kind == "txt"
        assert page.table.item(0, 2).text() == "已完成"
    finally:
        page.close()


def test_translation_error_marks_persisted_failed(qapp, tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_real_source(tmp_path), title="Novel")

    page = ProjectPage()
    try:
        page.set_project_manager(manager)
        page.refresh_projects()
        page._current_translation_row = 0
        page._translation_runner = MagicMock()

        with patch("ui.translation_studio.pages.project_page.QMessageBox"):
            page._on_translation_error("provider unavailable")

        reloaded = manager.load(project.project_id)
        assert reloaded.state.reader_status == "failed"
        # canonical derivation governs the card status; the failure surfaces as a note
        from ui.translation_studio.project_view_model import build_card_model

        assert build_card_model(reloaded).note == "翻譯失敗"
    finally:
        page.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
