"""S8-01 EPUB Translation Studio Direct Launch — UI acceptance coverage.

Covers the EPUB Project Page launch path from selection, through
EpubTranslationOptions routing, to success/incomplete/failed result states
and duplicate-launch protection.

No provider, network, or real translation execution is performed:
`_build_epub_options` and `TranslationRunner` are mocked.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import MappingProxyType
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.translation_studio.pages.project_page import ProjectPage
from core.epub_translation.runtime.adapter import EpubTranslationOptions
from core.epub_translation.contract import EpubMetadata, EpubTranslationInput


@pytest.fixture
def app():
    """Create QApplication instance."""
    return QApplication.instance() or QApplication(sys.argv)


@pytest.fixture
def project_page(app):
    """Create ProjectPage instance."""
    page = ProjectPage()
    yield page
    page.close()


def _add_epub_project(page: ProjectPage, source: str = "input/test.epub", name: str = "Test EPUB") -> dict:
    """Add an EPUB project (with chapter_map) to the page."""
    book_info = {
        "title": name,
        "source": source,
        "preview_text": "Chapter 1 content",
        "status": "success",
        "warnings": [],
        "chapter_map": [
            {"index": 1, "title": "Chapter 1", "start_offset": 0, "end_offset": 100}
        ],
    }
    page.add_project(
        name=name,
        source=source,
        status="已匯入",
        progress="0%",
        book_info=book_info,
    )
    return book_info


def _make_epub_options(source: str = "input/test.epub") -> EpubTranslationOptions:
    """Build a minimal real EpubTranslationOptions for routing assertions."""
    metadata = EpubMetadata(
        title="Test",
        author=None,
        language="ko",
        identifier="id-1",
        publisher=None,
        date=None,
        raw=MappingProxyType({}),
    )
    translation_input = EpubTranslationInput(
        source_epub_path=Path(source),
        original_hash="a" * 64,
        extraction_status="success",
        warnings=(),
        metadata=metadata,
        chapter_map=(),
        resources=(),
        toc_entries=(),
        fixed_layout_info=None,
    )
    return EpubTranslationOptions(translation_input=translation_input, chunks=())


def test_a_epub_translate_button_enabled(project_page):
    """Test A — EPUB project selection enables the Translate button."""
    _add_epub_project(project_page)

    project_page.table.selectRow(0)

    assert project_page.btn_translate.isEnabled(), "Translate button should be enabled for EPUB project"
    assert project_page.btn_translate.toolTip() == ""


def test_b_epub_launch_routes_to_epub_options(project_page):
    """Test B — EPUB launch routes through _build_epub_options, not the TXT path."""
    _add_epub_project(project_page)
    project_page.table.selectRow(0)

    options = _make_epub_options()

    with patch.object(project_page, "_build_epub_options", return_value=options) as mock_build, \
            patch("ui.translation_studio.pages.project_page.TranslationRunner") as mock_runner_cls, \
            patch("ui.translation_studio.pages.project_page.TxtTranslationOptions") as mock_txt:
        mock_runner = MagicMock()
        mock_runner_cls.return_value = mock_runner

        project_page._on_translate()

        assert mock_build.called, "_build_epub_options must be used for EPUB projects"
        assert not mock_txt.called, "TXT translation options must not be created for EPUB projects"
        assert mock_runner_cls.called, "TranslationRunner must be created"
        passed_options = mock_runner_cls.call_args[0][0]
        assert isinstance(passed_options, EpubTranslationOptions)
        assert mock_runner.start.called, "TranslationRunner.start must be invoked"


def test_c_epub_success_result(project_page):
    """Test C — EPUB success result maps to 翻譯完成 and resets state."""
    _add_epub_project(project_page)
    project_page.table.selectRow(0)
    project_page._current_translation_row = 0
    project_page._translation_runner = MagicMock()

    result = {
        "status": "success",
        "input": "input/test.epub",
        "output": "input/output/epub_translation/id-1/test_zh.epub",
        "output_dir": "input/output/epub_translation/id-1",
        "chunk_total": 5,
        "chunk_successful": 5,
        "chunk_failed": 0,
        "error": "",
        "summary": {"total_chunks": 5},
        "pipeline_mode": "epub",
        "session_id": "sess-1",
    }

    with patch("ui.translation_studio.pages.project_page.QMessageBox.information") as mock_info:
        project_page._on_translation_finished(result)

        assert project_page._projects[0]["status"] == "翻譯完成"
        assert "成功區塊：5 / 5" in project_page._projects[0]["progress"]
        assert project_page._current_translation_row is None
        assert project_page._translation_runner is None
        assert mock_info.call_count == 1
        message = mock_info.call_args[0][2]
        assert "test_zh.epub" in message, "Completion dialog must show the EPUB output path"


def test_d_epub_incomplete_result(project_page):
    """Test D — EPUB incomplete result maps to 翻譯未完成 (not success)."""
    _add_epub_project(project_page)
    project_page.table.selectRow(0)
    project_page._current_translation_row = 0
    project_page._translation_runner = MagicMock()

    result = {
        "status": "incomplete",
        "input": "input/test.epub",
        "output": "input/output/epub_translation/id-1/test_zh.epub",
        "chunk_total": 5,
        "chunk_successful": 3,
        "chunk_failed": 2,
        "error": "partial",
        "session_id": "sess-1",
    }

    with patch("ui.translation_studio.pages.project_page.QMessageBox.warning") as mock_warn:
        project_page._on_translation_finished(result)

        assert project_page._projects[0]["status"] == "翻譯未完成"
        assert "3/5 成功" in project_page._projects[0]["progress"]
        assert project_page._current_translation_row is None
        assert project_page._translation_runner is None
        mock_warn.assert_called_once()


def test_e_epub_failure_result(project_page):
    """Test E — EPUB failure result maps to 翻譯失敗."""
    _add_epub_project(project_page)
    project_page.table.selectRow(0)
    project_page._current_translation_row = 0
    project_page._translation_runner = MagicMock()

    result = {
        "status": "failed",
        "input": "input/test.epub",
        "output": "",
        "chunk_total": 5,
        "chunk_successful": 0,
        "chunk_failed": 5,
        "error": "EPUB translation failed",
        "session_id": "sess-1",
    }

    with patch("ui.translation_studio.pages.project_page.QMessageBox.critical") as mock_crit:
        project_page._on_translation_finished(result)

        assert project_page._projects[0]["status"] == "翻譯失敗"
        assert project_page._current_translation_row is None
        assert project_page._translation_runner is None
        mock_crit.assert_called_once()


def test_f_epub_duplicate_launch_blocked(project_page):
    """Test F — a second EPUB launch does not create a second runner."""
    _add_epub_project(project_page)
    project_page.table.selectRow(0)

    options = _make_epub_options()

    with patch.object(project_page, "_build_epub_options", return_value=options), \
            patch("ui.translation_studio.pages.project_page.TranslationRunner") as mock_runner_cls, \
            patch("ui.translation_studio.pages.project_page.QMessageBox.information"):
        mock_runner = MagicMock()
        mock_runner_cls.return_value = mock_runner

        # First launch
        project_page._on_translate()
        assert project_page._current_translation_row == 0
        assert mock_runner.start.called

        mock_runner.start.reset_mock()

        # Second launch attempt
        project_page._on_translate()
        assert not mock_runner.start.called, "Duplicate launch must not start a second translation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
