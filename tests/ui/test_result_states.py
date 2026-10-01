"""Test GUI result states for Translation Launch 01."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from PySide6.QtWidgets import QApplication

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import mock runtime first
sys.path.insert(0, str(ROOT / "tests" / "ui"))
from mock_translation_runtime import install_mock_runtime, MockTranslationRuntime

# Set up mock runtime BEFORE importing UI modules
install_mock_runtime()

from ui.translation_studio.pages.project_page import ProjectPage
from ui.translation_studio.translation_worker import TranslationWorker, TranslationRunner
from lts.txt_translation_runtime import TxtTranslationOptions


def create_test_setup():
    """Create test setup with app and project page."""
    app = QApplication.instance() or QApplication(sys.argv)
    project_page = ProjectPage()
    
    # Add a valid TXT project
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
    project_page.table.selectRow(0)
    
    return app, project_page


def mock_qmessagebox():
    """Mock QMessageBox to avoid blocking dialogs."""
    from PySide6.QtWidgets import QMessageBox
    return patch.multiple(
        QMessageBox,
        information=MagicMock(),
        warning=MagicMock(),
        critical=MagicMock(),
        question=MagicMock(return_value=QMessageBox.StandardButton.Yes),
    )


def test_success_state():
    """Test success result handling."""
    print("\n=== Testing SUCCESS state ===")
    app, project_page = create_test_setup()
    
    with mock_qmessagebox():
        # Set mock to success mode
        MockTranslationRuntime.set_result_mode("success")
        MockTranslationRuntime.set_chunk_total(3)
        MockTranslationRuntime.set_chunk_delay(0.1)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test.txt"
            input_path.write_text("Test content")
            output_dir = Path(tmpdir) / "output"
            
            options = TxtTranslationOptions(
                input_path=input_path,
                output_dir=output_dir,
                model="meta/llama-3.2-90b-vision-instruct",
                dry_run=False,
            )
            
            # Create worker and run
            worker = TranslationWorker(options, Path(tmpdir))
            worker.run()
            
            # Check result
            assert worker.is_finished()
            assert not worker.is_cancelled()
            
            # Verify final progress was emitted (would need signal capture in real test)
            # For now, verify the mock produces correct result
            from core.translation_runtime import TranslationRuntime
            runtime = TranslationRuntime(root=Path(tmpdir))
            result = runtime.translate_txt(options)
            
            assert result["status"] == "success"
            assert result["chunk_successful"] == 3
            assert result["chunk_failed"] == 0
            print("  [OK] Mock returns success result")
            
            # Test UI handler
            project_page._current_translation_row = 0
            project_page._on_translation_finished(result)
            
            assert project_page._projects[0]["status"] == "翻譯完成"
            assert "成功區塊：3 / 3" in project_page._projects[0]["progress"]
            assert project_page._current_translation_row is None
            assert project_page._translation_runner is None
            print("  [OK] UI handles success correctly: status='翻譯完成', buttons reset")
    
    project_page.close()
    print("  PASS: Success state verified")
    return True


def test_incomplete_state():
    """Test incomplete result handling."""
    print("\n=== Testing INCOMPLETE state ===")
    app, project_page = create_test_setup()
    
    with mock_qmessagebox():
        MockTranslationRuntime.set_result_mode("incomplete")
        MockTranslationRuntime.set_chunk_total(5)
        MockTranslationRuntime.set_chunk_delay(0.1)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test.txt"
            input_path.write_text("Test content")
            output_dir = Path(tmpdir) / "output"
            
            options = TxtTranslationOptions(
                input_path=input_path,
                output_dir=output_dir,
                model="meta/llama-3.2-90b-vision-instruct",
                dry_run=False,
            )
            
            from core.translation_runtime import TranslationRuntime
            runtime = TranslationRuntime(root=Path(tmpdir))
            result = runtime.translate_txt(options)
            
            assert result["status"] == "incomplete"
            assert result["chunk_successful"] == 3  # 5 - 2
            assert result["chunk_failed"] == 2
            print("  [OK] Mock returns incomplete result")
            
            # Test UI handler
            project_page._current_translation_row = 0
            project_page._on_translation_finished(result)
            
            assert project_page._projects[0]["status"] == "翻譯未完成"
            assert "3/5 成功" in project_page._projects[0]["progress"]
            assert project_page._current_translation_row is None
            assert project_page._translation_runner is None
            print("  [OK] UI handles incomplete correctly: status='翻譯未完成', buttons reset")
    
    project_page.close()
    print("  PASS: Incomplete state verified")
    return True


def test_failed_state():
    """Test failed result handling."""
    print("\n=== Testing FAILED state ===")
    app, project_page = create_test_setup()
    
    with mock_qmessagebox():
        MockTranslationRuntime.set_result_mode("failed")
        MockTranslationRuntime.set_chunk_total(5)
        MockTranslationRuntime.set_chunk_delay(0.1)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test.txt"
            input_path.write_text("Test content")
            output_dir = Path(tmpdir) / "output"
            
            options = TxtTranslationOptions(
                input_path=input_path,
                output_dir=output_dir,
                model="meta/llama-3.2-90b-vision-instruct",
                dry_run=False,
            )
            
            from core.translation_runtime import TranslationRuntime
            runtime = TranslationRuntime(root=Path(tmpdir))
            result = runtime.translate_txt(options)
            
            assert result["status"] == "failed"
            assert result["chunk_successful"] == 0
            assert result["chunk_failed"] == 5
            assert "error" in result
            print("  [OK] Mock returns failed result")
            
            # Test UI handler
            project_page._current_translation_row = 0
            project_page._on_translation_finished(result)
            
            assert project_page._projects[0]["status"] == "翻譯失敗"
            assert project_page._projects[0]["progress"] == "失敗"
            assert project_page._current_translation_row is None
            assert project_page._translation_runner is None
            print("  [OK] UI handles failed correctly: status='翻譯失敗', buttons reset")
    
    project_page.close()
    print("  PASS: Failed state verified")
    return True


def test_exception_state():
    """Test exception handling."""
    print("\n=== Testing EXCEPTION state ===")
    app, project_page = create_test_setup()
    
    with mock_qmessagebox():
        MockTranslationRuntime.set_result_mode("exception")
        MockTranslationRuntime.set_exception_message("Connection timeout to provider")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test.txt"
            input_path.write_text("Test content")
            output_dir = Path(tmpdir) / "output"
            
            options = TxtTranslationOptions(
                input_path=input_path,
                output_dir=output_dir,
                model="meta/llama-3.2-90b-vision-instruct",
                dry_run=False,
            )
            
            # Test worker exception handling
            worker = TranslationWorker(options, Path(tmpdir))
            worker.run()
            
            assert worker.is_finished()
            # Error signal should have been emitted
            print("  [OK] Worker handles exception, finishes without crash")
            
            # Test UI handler for exception
            project_page._current_translation_row = 0
            project_page._on_translation_error("Connection timeout to provider")
            
            assert project_page._projects[0]["status"] == "翻譯失敗"
            assert project_page._projects[0]["progress"] == "錯誤"
            assert project_page._current_translation_row is None
            assert project_page._translation_runner is None
            print("  [OK] UI handles exception correctly: status='翻譯失敗', buttons reset")
    
    project_page.close()
    print("  PASS: Exception state verified")
    return True


def test_worker_stops_polling():
    """Test worker stops polling timer in all states."""
    print("\n=== Testing WORKER POLLING STOP ===")
    
    for mode in ["success", "incomplete", "failed", "exception"]:
        MockTranslationRuntime.set_result_mode(mode)
        MockTranslationRuntime.set_chunk_total(2)
        MockTranslationRuntime.set_chunk_delay(0.05)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test.txt"
            input_path.write_text("Test content")
            output_dir = Path(tmpdir) / "output"
            
            options = TxtTranslationOptions(
                input_path=input_path,
                output_dir=output_dir,
                model="meta/llama-3.2-90b-vision-instruct",
                dry_run=False,
            )
            
            worker = TranslationWorker(options, Path(tmpdir))
            worker.run()
            
            assert not worker._poll_timer.isActive(), f"Polling timer should stop for {mode}"
            print(f"  [OK] Polling stopped for {mode}")
    
    print("  PASS: Worker polling stops in all states")
    return True


def test_runner_cleanup():
    """Test TranslationRunner cleanup after completion."""
    print("\n=== Testing RUNNER CLEANUP ===")
    app, project_page = create_test_setup()
    
    with mock_qmessagebox():
        MockTranslationRuntime.set_result_mode("success")
        MockTranslationRuntime.set_chunk_total(2)
        MockTranslationRuntime.set_chunk_delay(0.05)
        
        # Mock TranslationRunner to use real worker
        original_runner = project_page._translation_runner
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test.txt"
            input_path.write_text("Test content")
            output_dir = Path(tmpdir) / "output"
            
            options = TxtTranslationOptions(
                input_path=input_path,
                output_dir=output_dir,
                model="meta/llama-3.2-90b-vision-instruct",
                dry_run=False,
            )
            
            # Create real runner
            runner = TranslationRunner(options, Path(tmpdir))
            
            finished_result = {}
            
            def on_progress(p):
                pass
            
            def on_finished(r):
                finished_result.update(r)
            
            def on_error(e):
                pass
            
            runner.start(on_progress, on_finished, on_error)
            
            # Wait for completion
            import time
            max_wait = 50  # 5 seconds
            elapsed = 0
            while runner.is_running() and elapsed < max_wait:
                app.processEvents()
                time.sleep(0.1)
                elapsed += 1
            
            # Verify runner completed
            assert not runner.is_running(), "Runner thread should finish"
            assert runner.is_completed(), "Runner should be marked completed"
            assert finished_result.get("status") == "success", "Result should be success"
            print("  [OK] Runner completes and cleans up thread")
            
            runner.cancel()
    
    project_page.close()
    print("  PASS: Runner cleanup verified")
    return True


def test_ui_operable_after_completion():
    """Test UI remains operable after translation completes."""
    print("\n=== Testing UI OPERABLE AFTER COMPLETION ===")
    app, project_page = create_test_setup()
    
    with mock_qmessagebox():
        # Test each state leaves UI operable
        for mode in ["success", "incomplete", "failed"]:
            MockTranslationRuntime.set_result_mode(mode)
            MockTranslationRuntime.set_chunk_total(2)
            MockTranslationRuntime.set_chunk_delay(0.05)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                input_path = Path(tmpdir) / "test.txt"
                input_path.write_text("Test content")
                output_dir = Path(tmpdir) / "output"
                
                options = TxtTranslationOptions(
                    input_path=input_path,
                    output_dir=output_dir,
                    model="meta/llama-3.2-90b-vision-instruct",
                    dry_run=False,
                )
                
                from core.translation_runtime import TranslationRuntime
                runtime = TranslationRuntime(root=Path(tmpdir))
                result = runtime.translate_txt(options)
                
                project_page._current_translation_row = 0
                project_page._on_translation_finished(result)
                
                # Verify UI is operable: buttons re-enabled
                project_page.table.selectRow(0)
                app.processEvents()
                
                # After completion, translate button should be enabled again (for TXT)
                assert project_page.btn_translate.isEnabled(), f"Translate button should be enabled after {mode}"
                assert project_page.btn_preview.isEnabled(), f"Preview button should be enabled after {mode}"
                assert project_page._current_translation_row is None, f"Current row should be reset after {mode}"
                print(f"  [OK] UI operable after {mode}")
    
    project_page.close()
    print("  PASS: UI operable after all completion states")
    return True


def test_duplicate_launch_blocked_during_execution():
    """Test duplicate launch is blocked while translation is running."""
    print("\n=== Testing DUPLICATE LAUNCH BLOCKED ===")
    app, project_page = create_test_setup()
    
    with mock_qmessagebox():
        with patch('ui.translation_studio.pages.project_page.TranslationRunner') as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner.is_running.return_value = True
            mock_runner_class.return_value = mock_runner
            
            project_page.table.selectRow(0)
            
            # First launch
            project_page._on_translate()
            assert project_page._current_translation_row == 0
            assert mock_runner.start.called
            
            # Reset mock
            mock_runner.start.reset_mock()
            
            # Second launch attempt during execution
            project_page._on_translate()
            
            # Should not create second runner
            assert not mock_runner.start.called, "Should not start second translation"
            assert project_page._current_translation_row == 0, "Should remain on same row"
            print("  [OK] Duplicate launch blocked during execution")
    
    project_page.close()
    print("  PASS: Duplicate launch blocked")
    return True


def test_progress_json_parsing():
    """Test UI correctly parses various progress JSON formats."""
    print("\n=== Testing PROGRESS JSON PARSING ===")
    app, project_page = create_test_setup()
    
    project_page.table.selectRow(0)
    project_page._current_translation_row = 0
    
    # Test running progress
    project_page._on_translation_progress({
        "status": "running",
        "chunk_total": 10,
        "chunk_completed": 4,
        "message": "翻譯中..."
    })
    assert "已完成 4 / 10" in project_page._projects[0]["progress"]
    print("  [OK] Running progress parsed correctly")
    
    # Test completed progress
    project_page._on_translation_progress({
        "status": "completed",
        "chunk_total": 10,
        "chunk_completed": 10,
        "message": "翻譯完成：10/10"
    })
    assert "已完成 10 / 10" in project_page._projects[0]["progress"]
    print("  [OK] Completed progress parsed correctly")
    
    # Test incomplete progress
    project_page._on_translation_progress({
        "status": "incomplete",
        "chunk_total": 10,
        "chunk_completed": 7,
        "chunk_failed": 3,
        "message": "翻譯未完成：7/10 成功，3 失敗"
    })
    assert "未完成" in project_page._projects[0]["progress"]
    print("  [OK] Incomplete progress parsed correctly")
    
    # Test failed progress
    project_page._on_translation_progress({
        "status": "failed",
        "chunk_total": 10,
        "chunk_completed": 0,
        "error": "Connection failed",
        "message": "翻譯失敗：Connection failed"
    })
    assert project_page._projects[0]["progress"] == "失敗"
    print("  [OK] Failed progress parsed correctly")
    
    # Test missing fields (robustness)
    project_page._on_translation_progress({"status": "running"})
    assert project_page._projects[0]["progress"] == "翻譯中..."
    print("  [OK] Missing fields handled gracefully")
    
    project_page.close()
    print("  PASS: Progress JSON parsing verified")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("TRANSLATION LAUNCH 01 - RESULT STATE GUI VERIFICATION")
    print("=" * 60)
    
    all_passed = True
    
    try:
        all_passed &= test_success_state()
        all_passed &= test_incomplete_state()
        all_passed &= test_failed_state()
        all_passed &= test_exception_state()
        all_passed &= test_worker_stops_polling()
        all_passed &= test_runner_cleanup()
        all_passed &= test_ui_operable_after_completion()
        all_passed &= test_duplicate_launch_blocked_during_execution()
        all_passed &= test_progress_json_parsing()
    except Exception as e:
        print(f"\n[FAIL] TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[PASS] ALL RESULT STATE TESTS PASSED")
    else:
        print("[FAIL] SOME TESTS FAILED")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)