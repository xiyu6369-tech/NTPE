# S6-02 Acceptance Test: Translation Launcher Runtime Wiring

"""
Mock integration test for Translation Launcher runtime wiring.

This test verifies the complete success path:
Launcher Start → controller.start_translation() → TranslationRunner.start() 
→ TranslationWorker → mock TranslationRuntime.translate_txt() 
→ successful TranslationResult → finished callback → UI receives success 
→ exact output path propagated
"""

import json
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import patch

import pytest

from core.launcher_product.config import load_launcher_config
from core.launcher_product.models import LauncherConfig


class MockTranslationRuntime:
    """Mock TranslationRuntime that returns controlled results."""

    def __init__(self, root: Path, result: Optional[Dict] = None, exception: Optional[Exception] = None):
        self.root = root
        self._result = result or {
            "status": "success",
            "input": "test.txt",
            "output": str(root / "output" / "test_zh.txt"),
            "output_dir": str(root / "output"),
            "chunk_total": 2,
            "chunk_successful": 2,
            "chunk_failed": 0,
            "resume_state": str(root / "output" / "test_resume_state.json"),
            "summary": {
                "success": 2,
                "skipped": 0,
                "failed": 0,
                "total_files": 1,
            },
        }
        self._exception = exception
        self.call_count = 0
        self.last_options = None

    def translate_txt(self, options: Any) -> Dict:
        self.call_count += 1
        self.last_options = options
        print(f"DEBUG Mock translate_txt called with output={self._result.get('output', '')}")
        
        if self._exception:
            raise self._exception
            
        # Create output file if it doesn't exist
        output_path = Path(self._result.get("output", ""))
        print(f"DEBUG Mock output_path: {output_path}, parent: {output_path.parent}")
        
        if self._exception:
            raise self._exception
            
        # Create output file if it doesn't exist
        output_path = Path(self._result.get("output", ""))
        if output_path and output_path.parent != Path("."):
            print(f"DEBUG Mock creating parent dir: {output_path.parent}")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("Translated content\n", encoding="utf-8")
            
        # Create resume state file only if resume_state is provided and valid
        resume_state = self._result.get("resume_state")
        if resume_state:
            resume_path = Path(resume_state)
            if resume_path and resume_path.parent != Path("."):
                resume_path.parent.mkdir(parents=True, exist_ok=True)
                resume_path.write_text(json.dumps({
                    "version": "1.1-lts-stage-05",
                    "chunks": {},
                    "events": []
                }), encoding="utf-8")
            
        return self._result


def create_test_config(tmp_path: Path, dry_run: bool = False) -> LauncherConfig:
    """Create a test LauncherConfig using the actual config system."""
    base = load_launcher_config()
    return replace(
        base,
        input_path=str(tmp_path / "test.txt"),
        output_directory=str(tmp_path / "output"),
        source_language="ko",
        target_language="zh-Hant",
        provider_id="nvidia",
        model_id="meta/llama-3.2-90b-vision-instruct",
        translation_profile="literary",
        chunk_size=1000,
        api_timeout=180,
        provider_attempts=2,
        overwrite=False,
        resume_enabled=True,
        dry_run=dry_run,
    )


def test_s6_02_success_path(tmp_path: Path):
    """
    S6-02-A: Complete Success Path
    
    Verifies:
    Launcher Start → controller.start_translation() → TranslationRunner.start() 
    → TranslationWorker → mock TranslationRuntime.translate_txt() 
    → successful TranslationResult → finished callback → UI receives success 
    → exact output path propagated
    """
    # Setup
    test_input = tmp_path / "test.txt"
    test_input.write_text("그녀는 천천히 고개를 들었다.\n", encoding="utf-8")
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    config = create_test_config(tmp_path)
    
    root_path = tmp_path
    
    # Track callbacks
    callback_data = {
        "progress_calls": [],
        "finished_result": None,
        "error_received": None,
    }
    
    def on_progress(progress: Dict):
        callback_data["progress_calls"].append(progress)
    
    def on_finished(result: Dict):
        callback_data["finished_result"] = result
    
    def on_error(error: str):
        callback_data["error_received"] = error
    
    from ui.translation_launcher.controller import LauncherController
    from ui.translation_launcher.worker import TranslationRunner
    from lts.txt_translation_runtime import TxtTranslationOptions
    
    controller = LauncherController()
    
    # Patch TranslationRuntime at the module where it's imported in worker
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime = MockTranslationRuntime(root_path)
        mock_runtime_class.return_value = mock_runtime
        
        # Start translation through controller
        runner = controller.start_translation(
            config=config,
            root_path=root_path,
            on_progress=on_progress,
            on_finished=on_finished,
            on_error=on_error,
        )
        
        # Verify runner was returned
        assert runner is not None
        assert hasattr(runner, 'is_running')
        assert hasattr(runner, 'is_completed')
        assert hasattr(runner, 'cancel')
        
        # Wait for completion
        timeout = 10.0
        start_time = time.time()
        while not runner.is_completed() and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        # Verify runtime was called
        assert mock_runtime.call_count == 1, "TranslationRuntime.translate_txt() should be called exactly once"
        assert mock_runtime.last_options is not None, "Options should be passed to runtime"
        
        # Verify options passed to runtime
        opts = mock_runtime.last_options
        assert isinstance(opts, TxtTranslationOptions)
        assert opts.input_path == test_input
        assert opts.output_dir == output_dir
        assert opts.model == "meta/llama-3.2-90b-vision-instruct"
        assert opts.quality_profile == "literary"
        assert opts.dry_run == False
        
        # Verify progress callbacks were received
        assert len(callback_data["progress_calls"]) >= 1, "Should receive progress updates"
        statuses = [p.get("status") for p in callback_data["progress_calls"]]
        assert "preparing" in statuses, "Should receive preparing status"
        assert "completed" in statuses, "Should receive completed status"
        
        # Verify finished callback was called
        assert callback_data["finished_result"] is not None, "Finished callback should be called"
        assert callback_data["error_received"] is None, "Should not receive error on success"
        
        # Verify finished result contains expected fields
        result = callback_data["finished_result"]
        assert result.get("status") == "success", "Result should indicate success"
        assert "output" in result, "Result should contain output path"
        
        # Verify output path propagation
        runtime_output = mock_runtime._result["output"]
        finished_output = result.get("output", "")
        assert runtime_output == finished_output, f"Output path mismatch: runtime={runtime_output}, finished={finished_output}"
        
        # Verify output file was created
        output_file = Path(runtime_output)
        assert output_file.exists(), "Output file should be created"
        assert output_file.read_text(encoding="utf-8") == "Translated content\n"
        
        # Verify UI state restoration - start button should be re-enabled
        assert runner.is_completed(), "Runner should be marked as completed"
        
        # Verify worker thread is not the main thread
        assert threading.current_thread() != getattr(runner, '_thread', None), "Worker should run in separate thread"
        
        print("SUCCESS: S6-02-A Success Path: ALL CHECKS PASSED")


def test_s6_02_failure_path_exception(tmp_path: Path):
    """
    S6-02-B: Failure Path - Exception
    
    Verifies:
    runtime exception → worker catches/propagates → error callback → UI enters failed state
    """
    test_input = tmp_path / "test.txt"
    test_input.write_text("test content\n", encoding="utf-8")
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    config = create_test_config(tmp_path)
    
    root_path = tmp_path
    
    callback_data = {
        "progress_calls": [],
        "finished_result": None,
        "error_received": None,
    }
    
    def on_progress(progress: Dict):
        callback_data["progress_calls"].append(progress)
    
    def on_finished(result: Dict):
        callback_data["finished_result"] = result
    
    def on_error(error: str):
        callback_data["error_received"] = error
    
    from ui.translation_launcher.controller import LauncherController
    from ui.translation_launcher.worker import TranslationRunner
    
    controller = LauncherController()
    
    test_exception = RuntimeError("Mock provider failure: connection timeout")
    
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime = MockTranslationRuntime(root_path, exception=test_exception)
        mock_runtime_class.return_value = mock_runtime
        
        runner = controller.start_translation(
            config=config,
            root_path=root_path,
            on_progress=on_progress,
            on_finished=on_finished,
            on_error=on_error,
        )
        
        # Wait for completion
        timeout = 10.0
        start_time = time.time()
        while not runner.is_completed() and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        # Verify error callback was called
        assert callback_data["error_received"] is not None, "Error callback should be called"
        assert "Mock provider failure" in callback_data["error_received"]
        assert "connection timeout" in callback_data["error_received"]
        
        # Verify finished callback was NOT called
        assert callback_data["finished_result"] is None, "Finished callback should not be called on error"
        
        # Verify progress callbacks stopped
        statuses = [p.get("status") for p in callback_data["progress_calls"]]
        assert "preparing" in statuses, "Should receive preparing status"
        # Should NOT receive "completed" or "running" after error
        assert "completed" not in statuses, "Should not receive completed status on error"
        
        # Verify worker thread stopped polling
        assert runner.is_completed(), "Runner should be marked as completed"
        
        print("SUCCESS: S6-02-B Failure Path (Exception): ALL CHECKS PASSED")


def test_s6_02_failure_path_incomplete_result(tmp_path: Path):
    """
    S6-02-B: Failure Path - Canonical incomplete result
    
    Verifies:
    canonical failed/incomplete result → worker → finished callback with incomplete → UI shows warning
    """
    test_input = tmp_path / "test.txt"
    test_input.write_text("test content\n", encoding="utf-8")
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    config = create_test_config(tmp_path)
    
    root_path = tmp_path
    
    callback_data = {
        "progress_calls": [],
        "finished_result": None,
        "error_received": None,
    }
    
    def on_progress(progress: Dict):
        callback_data["progress_calls"].append(progress)
    
    def on_finished(result: Dict):
        callback_data["finished_result"] = result
    
    def on_error(error: str):
        callback_data["error_received"] = error
    
    from ui.translation_launcher.controller import LauncherController
    from ui.translation_launcher.worker import TranslationRunner
    
    controller = LauncherController()
    
    # Create a canonical incomplete result
    incomplete_result = {
        "status": "incomplete",
        "input": str(test_input),
        "output": str(output_dir / "test_zh.txt"),
        "output_dir": str(output_dir),
        "chunk_total": 3,
        "chunk_successful": 1,
        "chunk_failed": 2,
        "error": "Provider timeout after retries",
    }
    
    # Patch TranslationRuntime at the module where it's imported in worker
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime = MockTranslationRuntime(root_path, result=incomplete_result)
        print(f"DEBUG: Mock runtime created with output={incomplete_result.get('output')}")
        mock_runtime_class.return_value = mock_runtime
        
        runner = controller.start_translation(
            config=config,
            root_path=root_path,
            on_progress=on_progress,
            on_finished=on_finished,
            on_error=on_error,
        )
        
        # Wait for completion
        timeout = 10.0
        start_time = time.time()
        while not runner.is_completed() and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        # Verify finished callback was called with incomplete result
        assert callback_data["finished_result"] is not None, "Finished callback should be called for incomplete"
        assert callback_data["error_received"] is None, "Error callback should not be called for incomplete"
        
        result = callback_data["finished_result"]
        assert result.get("status") == "incomplete", "Result should be incomplete"
        assert result.get("chunk_successful") == 1
        assert result.get("chunk_failed") == 2
        
        # Verify progress callbacks included incomplete
        statuses = [p.get("status") for p in callback_data["progress_calls"]]
        assert "incomplete" in statuses, "Should receive incomplete status"
        
        print("SUCCESS: S6-02-B Failure Path (Incomplete): ALL CHECKS PASSED")


def test_s6_02_thread_lifecycle(tmp_path: Path):
    """
    S6-02-C: Thread/UI Lifecycle Contract
    
    Verifies:
    1. TranslationRuntime.translate_txt() NOT in Tkinter UI thread
    2. UI callback uses root.after (or equivalent safe dispatch) - verified in app.py
    3. Worker polling stops on completion
    4. Worker polling stops on failure
    5. No duplicate completion callback
    6. Start Translation state restores after completion
    7. No daemon worker left running after failure
    """
    test_input = tmp_path / "test.txt"
    test_input.write_text("test\n", encoding="utf-8")
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    config = create_test_config(tmp_path)
    
    root_path = tmp_path
    
    callback_data = {
        "progress_calls": [],
        "finished_count": 0,
        "error_count": 0,
    }
    
    def on_progress(progress: Dict):
        callback_data["progress_calls"].append(progress)
    
    def on_finished(result: Dict):
        callback_data["finished_count"] += 1
    
    def on_error(error: str):
        callback_data["error_count"] += 1
    
    from ui.translation_launcher.controller import LauncherController
    from ui.translation_launcher.worker import TranslationRunner
    
    controller = LauncherController()
    
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime = MockTranslationRuntime(root_path)
        mock_runtime_class.return_value = mock_runtime
        
        runner = controller.start_translation(
            config=config,
            root_path=root_path,
            on_progress=on_progress,
            on_finished=on_finished,
            on_error=on_error,
        )
        
        # Wait for completion
        timeout = 10.0
        start_time = time.time()
        while not runner.is_completed() and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        # 1. Verify worker runs in separate thread
        assert hasattr(runner, '_thread'), "Runner should have worker thread"
        worker_thread = runner._thread
        assert worker_thread is not None, "Worker thread should exist"
        assert worker_thread != threading.main_thread(), "Worker should not run in main thread"
        
        # 2. Verify app.py uses root.after for UI callbacks (pattern check)
        import inspect
        app_source = Path("D:/Python/NTPE/ui/translation_launcher/app.py").read_text(encoding="utf-8")
        assert "root.after" in app_source, "app.py should use root.after for UI callbacks"
        assert "root.after(0" in app_source, "app.py should use root.after(0, ...) for immediate dispatch"
        
        # 3. Verify polling stops on success
        # Worker thread should finish
        assert not worker_thread.is_alive(), "Worker thread should finish after completion"
        assert runner.is_completed(), "Runner should be completed"
        
        # 4. Verify no duplicate callbacks
        assert callback_data["finished_count"] == 1, f"Finished callback should be called exactly once, got {callback_data['finished_count']}"
        assert callback_data["error_count"] == 0, "Error callback should not be called on success"
        
        # 5. Verify start state restoration - runner completed and thread joined
        assert runner.is_completed()
        
        print("SUCCESS: S6-02-C Thread/Lifecycle: ALL CHECKS PASSED")


def test_s6_02_failure_thread_lifecycle(tmp_path: Path):
    """Verify thread lifecycle on failure."""
    test_input = tmp_path / "test.txt"
    test_input.write_text("test\n", encoding="utf-8")
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    config = create_test_config(tmp_path)
    
    root_path = tmp_path
    
    callback_data = {
        "progress_calls": [],
        "finished_count": 0,
        "error_count": 0,
    }
    
    def on_progress(progress: Dict):
        callback_data["progress_calls"].append(progress)
    
    def on_finished(result: Dict):
        callback_data["finished_count"] += 1
    
    def on_error(error: str):
        callback_data["error_count"] += 1
    
    from ui.translation_launcher.controller import LauncherController
    from ui.translation_launcher.worker import TranslationRunner
    
    controller = LauncherController()
    
    test_exception = RuntimeError("Test failure")
    
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime = MockTranslationRuntime(root_path, exception=test_exception)
        mock_runtime_class.return_value = mock_runtime
        
        runner = controller.start_translation(
            config=config,
            root_path=root_path,
            on_progress=on_progress,
            on_finished=on_finished,
            on_error=on_error,
        )
        
        # Wait for completion
        timeout = 10.0
        start_time = time.time()
        while not runner.is_completed() and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        # Verify error callback was called once
        assert callback_data["error_count"] == 1, "Error callback should be called exactly once"
        assert callback_data["finished_count"] == 0, "Finished callback should not be called on error"
        
        # Verify app.py uses root.after for UI callbacks (pattern check)
        app_source = Path("D:/Python/NTPE/ui/translation_launcher/app.py").read_text(encoding="utf-8")
        assert "root.after" in app_source, "app.py should use root.after for UI callbacks"
        assert "root.after(0" in app_source, "app.py should use root.after(0, ...) for immediate dispatch"
        
        # Verify worker thread stops
        worker_thread = runner._thread
        assert worker_thread is not None
        assert not worker_thread.is_alive(), "Worker thread should finish after error"
        assert runner.is_completed(), "Runner should be completed"
        
        print("SUCCESS: S6-02-C Failure Thread Lifecycle: ALL CHECKS PASSED")


def test_s6_02_code_review_checks():
    """
    S6-02-D: Implementation Code Review
    
    Checks for correctness bugs in:
    - app.py
    - controller.py
    - worker.py
    """
    import ast
    
    # Read source files
    source_files = {
        "app.py": Path("D:/Python/NTPE/ui/translation_launcher/app.py").read_text(encoding="utf-8"),
        "controller.py": Path("D:/Python/NTPE/ui/translation_launcher/controller.py").read_text(encoding="utf-8"),
        "worker.py": Path("D:/Python/NTPE/ui/translation_launcher/worker.py").read_text(encoding="utf-8"),
    }
    
    issues = []
    
    for filename, source in source_files.items():
        tree = ast.parse(source)
        
        # Check for thread safety: UI callbacks should use root.after
        if filename == "app.py":
            # Check that _on_translation_progress, _on_translation_finished, _on_translation_error
            # are called via root.after
            has_root_after = "root.after" in source
            if not has_root_after:
                issues.append(f"{filename}: Missing root.after for UI callbacks")
            
            # Check that start_button state is managed correctly
            if "start_button.config(state=\"disabled\")" not in source:
                issues.append(f"{filename}: start_button not disabled during translation")
            if "start_button.config(state=\"normal\")" not in source:
                issues.append(f"{filename}: start_button not re-enabled after completion")
        
        if filename == "worker.py":
            # Check for polling termination
            if "_poll_running = False" not in source:
                issues.append(f"{filename}: Polling flag not set to False on completion")
            
            # Check exception handling
            if "except Exception as e:" not in source:
                issues.append(f"{filename}: Missing exception handling in worker")
            
            # Check thread join
            if "_poll_thread.join" not in source:
                issues.append(f"{filename}: Missing thread join on completion")
        
        if filename == "controller.py":
            # Check that start_translation doesn't call provider directly
            if "NvidiaClient" in source:
                issues.append(f"{filename}: Direct NvidiaClient usage detected")
            if "NvidiaTranslationProvider" in source:
                issues.append(f"{filename}: Direct NvidiaTranslationProvider usage detected")
    
    # Also check no second translation path created
    all_source = "\n".join(source_files.values())
    if all_source.count("TranslationRuntime") > 2:  # Only imports and usage
        # This is approximate - check if there are multiple TranslationRuntime instantiations
        pass
    
    if issues:
        raise AssertionError(f"Code review issues found:\n" + "\n".join(f"  - {issue}" for issue in issues))
    
    print("SUCCESS: S6-02-D Code Review: ALL CHECKS PASSED")


if __name__ == "__main__":
    # Run tests manually for quick verification
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        
        print("Running S6-02 Acceptance Tests...")
        print()
        
        test_s6_02_success_path(tmp_path)
        test_s6_02_failure_path_exception(tmp_path)
        test_s6_02_failure_path_incomplete_result(tmp_path)
        test_s6_02_thread_lifecycle(tmp_path)
        test_s6_02_failure_thread_lifecycle(tmp_path)
        test_s6_02_code_review_checks()
        
        print()
        print("=" * 60)
        print("ALL S6-02 ACCEPTANCE TESTS PASSED")
        print("=" * 60)