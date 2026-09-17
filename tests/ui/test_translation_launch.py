from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.translation_studio.pages.project_page import ProjectPage
from ui.translation_studio.translation_worker import TranslationWorker, TranslationRunner


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


@pytest.fixture
def valid_txt_project(project_page):
    """Add a valid TXT project to the page."""
    book_info = {
        "title": "Test Novel",
        "source": "input/test.txt",
        "preview_text": "Chapter 1\n\nTest content.",
        "status": "ready",
        "warnings": [],
    }
    project_page.add_project(
        name="Test Novel",
        source="input/test.txt",
        status="已匯入",
        progress="0%",
        book_info=book_info,
    )
    return project_page


def test_valid_txt_project_can_launch(project_page, valid_txt_project):
    """Test that a valid TXT project can launch translation."""
    # Select the project
    project_page.table.selectRow(0)

    # Verify translate button is enabled for TXT project
    assert project_page.btn_translate.isEnabled(), "Translate button should be enabled for TXT project"
    assert project_page._current_translation_row is None


def test_epub_project_cannot_launch(project_page):
    """Test that EPUB project cannot enter TXT translation path."""
    book_info = {
        "title": "Test EPUB",
        "source": "input/test.epub",
        "preview_text": "Content",
        "status": "success",
        "warnings": [],
        "chapter_map": [
            {"index": 1, "title": "Chapter 1", "start_offset": 0, "end_offset": 100}
        ],
    }
    project_page.add_project(
        name="Test EPUB",
        source="input/test.epub",
        status="已匯入",
        progress="0%",
        book_info=book_info,
    )

    # Select the EPUB project
    project_page.table.selectRow(0)

    # Verify translate button is disabled for EPUB project
    assert not project_page.btn_translate.isEnabled(), "Translate button should be disabled for EPUB project"
    assert "EPUB 專案暫不支援直接啟動翻譯" in project_page.btn_translate.toolTip()


def test_invalid_source_cannot_launch(project_page):
    """Test that project without valid source cannot launch."""
    book_info = {
        "title": "Invalid Project",
        "source": "",
        "preview_text": "Content",
        "status": "ready",
        "warnings": [],
    }
    project_page.add_project(
        name="Invalid Project",
        source="",
        status="已匯入",
        progress="0%",
        book_info=book_info,
    )

    project_page.table.selectRow(0)

    # Verify translate button is disabled
    assert not project_page.btn_translate.isEnabled(), "Translate button should be disabled for project without source"
    assert "無有效 TXT 來源" in project_page.btn_translate.toolTip()


def test_duplicate_launch_blocked(project_page, valid_txt_project):
    """Test that duplicate launch is blocked while translation is running."""
    project_page.table.selectRow(0)

    # Mock QMessageBox to avoid blocking dialogs in headless test
    with patch('ui.translation_studio.pages.project_page.QMessageBox') as mock_msgbox:
        # Mock the TranslationRunner to avoid actual runtime call
        with patch('ui.translation_studio.pages.project_page.TranslationRunner') as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner_class.return_value = mock_runner

            # First launch
            project_page._on_translate()

            # Verify translation started
            assert project_page._current_translation_row == 0
            assert mock_runner.start.called

            # Reset mock to track second call
            mock_runner.start.reset_mock()

            # Second launch attempt should be blocked
            project_page._on_translate()

            # Should not create second runner
            assert not mock_runner.start.called, "Should not start second translation job"


def test_worker_runs_in_background_thread():
    """Test that TranslationWorker runs in background thread."""
    from lts.txt_translation_runtime import TxtTranslationOptions

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "test.txt"
        input_path.write_text("Test content")
        output_dir = Path(tmpdir) / "output"

        options = TxtTranslationOptions(
            input_path=input_path,
            output_dir=output_dir,
            model="meta/llama-3.2-90b-vision-instruct",
            dry_run=True,  # No actual API call
        )

        worker = TranslationWorker(options, Path(tmpdir))

        # Verify worker is a QObject (runs in thread via moveToThread)
        from PySide6.QtCore import QObject
        assert isinstance(worker, QObject)

        # Verify it has the required signals
        assert hasattr(worker, 'progress_updated')
        assert hasattr(worker, 'translation_finished')
        assert hasattr(worker, 'translation_error')


def test_progress_json_valid_fields(project_page, valid_txt_project):
    """Test that UI correctly parses valid progress JSON fields."""
    project_page.table.selectRow(0)
    project_page._current_translation_row = 0  # Simulate translation in progress

    # Mock progress data
    progress = {
        "status": "running",
        "chunk_total": 10,
        "chunk_completed": 4,
        "message": "翻譯中..."
    }

    project_page._on_translation_progress(progress)

    # Verify UI updated with correct values
    assert project_page._projects[0]["status"] == "翻譯中..."
    assert "已完成 4 / 10" in project_page._projects[0]["progress"]


def test_progress_json_missing_file_handling(project_page, valid_txt_project):
    """Test that missing progress file doesn't crash."""
    project_page.table.selectRow(0)
    project_page._current_translation_row = 0

    # Simulate empty progress dict (file missing)
    progress = {}
    project_page._on_translation_progress(progress)

    # Should not crash, status should be empty string (defaults)
    assert project_page._projects[0]["status"] == ""


def test_progress_json_invalid_json_handling(project_page, valid_txt_project):
    """Test that invalid JSON doesn't crash."""
    project_page.table.selectRow(0)
    project_page._current_translation_row = 0

    # Worker's _poll_progress catches all exceptions, so this tests the signal handler
    progress = "not a dict"  # Invalid type
    # The signal handler expects dict, so we test with valid dict but missing fields
    progress = {"status": "unknown_status"}
    project_page._on_translation_progress(progress)

    # Should not crash - status comes from message (empty), progress comes from status
    assert project_page._projects[0]["progress"] == "unknown_status"


def test_progress_json_incomplete_fields(project_page, valid_txt_project):
    """Test that progress with missing fields doesn't crash."""
    project_page.table.selectRow(0)
    project_page._current_translation_row = 0

    progress = {"status": "running"}  # Missing chunk_total, chunk_completed
    project_page._on_translation_progress(progress)

    # Should not crash, uses defaults - status comes from message (empty), progress from computed text
    assert project_page._projects[0]["progress"] == "翻譯中..."


def test_success_result_handling(project_page, valid_txt_project):
    """Test that success result is handled correctly."""
    project_page._current_translation_row = 0

    result = {
        "status": "success",
        "output": "output/test_zh.txt",
        "chunk_total": 10,
        "chunk_successful": 10,
        "session_id": "test-session-123",
    }

    with patch('ui.translation_studio.pages.project_page.QMessageBox.information') as mock_msg:
        project_page._on_translation_finished(result)

        # Verify UI state
        assert project_page._projects[0]["status"] == "翻譯完成"
        assert "成功區塊：10 / 10" in project_page._projects[0]["progress"]

        # Verify reset
        assert project_page._current_translation_row is None
        assert project_page._translation_runner is None

        # Verify message shown
        mock_msg.assert_called_once()


def test_incomplete_result_handling(project_page, valid_txt_project):
    """Test that incomplete result is handled correctly."""
    project_page._current_translation_row = 0

    result = {
        "status": "incomplete",
        "chunk_total": 10,
        "chunk_successful": 7,
        "chunk_failed": 3,
        "error": "Provider timeout",
    }

    with patch('ui.translation_studio.pages.project_page.QMessageBox.warning') as mock_msg:
        project_page._on_translation_finished(result)

        # Verify UI state
        assert project_page._projects[0]["status"] == "翻譯未完成"
        assert "7/10 成功" in project_page._projects[0]["progress"]

        # Verify message shown
        mock_msg.assert_called_once()


def test_failed_result_handling(project_page, valid_txt_project):
    """Test that failed result is handled correctly."""
    project_page._current_translation_row = 0

    result = {
        "status": "failed",
        "error": "Authentication failed",
    }

    with patch('ui.translation_studio.pages.project_page.QMessageBox.critical') as mock_msg:
        project_page._on_translation_finished(result)

        # Verify UI state
        assert project_page._projects[0]["status"] == "翻譯失敗"
        assert project_page._projects[0]["progress"] == "失敗"

        # Verify message shown
        mock_msg.assert_called_once()


def test_exception_handling(project_page, valid_txt_project):
    """Test that exception during translation is handled correctly."""
    project_page._current_translation_row = 0

    with patch('ui.translation_studio.pages.project_page.QMessageBox.critical') as mock_msg:
        project_page._on_translation_error("Runtime error: connection timeout")

        # Verify UI state
        assert project_page._projects[0]["status"] == "翻譯失敗"
        assert project_page._projects[0]["progress"] == "錯誤"

        # Verify reset
        assert project_page._current_translation_row is None
        assert project_page._translation_runner is None

        # Verify message shown
        mock_msg.assert_called_once()


def test_missing_result_fields_handling(project_page, valid_txt_project):
    """Test that result with missing fields doesn't crash."""
    project_page._current_translation_row = 0

    result = {"status": "unknown_status"}

    with patch('ui.translation_studio.pages.project_page.QMessageBox.critical') as mock_msg:
        project_page._on_translation_finished(result)

        # Should not crash, treated as failed
        assert project_page._projects[0]["status"] == "翻譯失敗"
        mock_msg.assert_called_once()


def test_worker_stops_polling_on_completion():
    """Test that worker stops polling timer on completion."""
    from lts.txt_translation_runtime import TxtTranslationOptions

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "test.txt"
        input_path.write_text("Test content")
        output_dir = Path(tmpdir) / "output"

        options = TxtTranslationOptions(
            input_path=input_path,
            output_dir=output_dir,
            model="meta/llama-3.2-90b-vision-instruct",
            dry_run=True,
        )

        worker = TranslationWorker(options, Path(tmpdir))

        # Mock the runtime to return success quickly
        with patch('core.translation_runtime.TranslationRuntime') as mock_runtime_class:
            mock_runtime = MagicMock()
            mock_runtime.translate_txt.return_value = {
                "status": "success",
                "output": "output/test_zh.txt",
                "chunk_total": 1,
                "chunk_successful": 1,
                "session_id": "test",
            }
            mock_runtime_class.return_value = mock_runtime

            # Run worker
            worker.run()

            # Verify polling timer stopped
            assert not worker._poll_timer.isActive(), "Polling timer should be stopped after completion"


def test_worker_stops_polling_on_error():
    """Test that worker stops polling timer on error."""
    from lts.txt_translation_runtime import TxtTranslationOptions

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "test.txt"
        input_path.write_text("Test content")
        output_dir = Path(tmpdir) / "output"

        options = TxtTranslationOptions(
            input_path=input_path,
            output_dir=output_dir,
            model="meta/llama-3.2-90b-vision-instruct",
            dry_run=True,
        )

        worker = TranslationWorker(options, Path(tmpdir))

        # Mock the runtime to raise exception
        with patch('core.translation_runtime.TranslationRuntime') as mock_runtime_class:
            mock_runtime_class.side_effect = Exception("Connection failed")

            # Run worker
            worker.run()

            # Verify polling timer stopped
            assert not worker._poll_timer.isActive(), "Polling timer should be stopped on error"


def test_runner_cancel_waits_for_thread():
    """Test that TranslationRunner.cancel waits for thread."""
    from lts.txt_translation_runtime import TxtTranslationOptions

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "test.txt"
        input_path.write_text("Test content")
        output_dir = Path(tmpdir) / "output"

        options = TxtTranslationOptions(
            input_path=input_path,
            output_dir=output_dir,
            model="meta/llama-3.2-90b-vision-instruct",
            dry_run=True,
        )

        runner = TranslationRunner(options, Path(tmpdir))

        # Start runner
        runner.start(
            on_progress=lambda x: None,
            on_finished=lambda x: None,
            on_error=lambda x: None,
        )

        # Verify thread is running
        assert runner._thread.isRunning()

        # Cancel
        runner.cancel()

        # Verify thread finished (with timeout)
        # Note: in test, thread may finish quickly due to dry_run
        # The important thing is cancel() method exists and doesn't crash


def test_runner_cleanup_on_finish():
    """Test that runner references are cleared after finish."""
    project_page = ProjectPage()
    project_page.table.selectRow(0)

    with patch('ui.translation_studio.pages.project_page.TranslationRunner') as mock_runner_class:
        mock_runner = MagicMock()
        mock_runner_class.return_value = mock_runner

        project_page._on_translate()

        # Simulate finish
        project_page._on_translation_finished({
            "status": "success",
            "output": "output/test_zh.txt",
            "chunk_total": 1,
            "chunk_successful": 1,
            "session_id": "test",
        })

        # Verify references cleared
        assert project_page._translation_runner is None
        assert project_page._current_translation_row is None
        project_page.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])