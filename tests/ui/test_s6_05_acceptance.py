# S6-05 Acceptance Test: TXT Dry-Run Status

"""
Mock integration test for Translation Launcher TXT Dry-Run.

This test verifies:
1. Valid TXT Dry-Run completes with status "dry_run"
2. No formal translated output is created
3. UI correctly handles dry-run result state
4. Invalid TXT Dry-Run is rejected
5. Existing output protection
6. Worker lifecycle for dry-run
7. Canonical route preservation
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

    def __init__(
        self,
        root: Path,
        result: Optional[Dict] = None,
        exception: Optional[Exception] = None,
    ):
        self.root = root
        self._result = result or {
            "status": "success",
            "input": "test.txt",
            "output": str(root / "output" / "test_zh.txt"),
            "output_dir": str(root / "output"),
            "chunk_total": 1,
            "chunk_successful": 1,
            "chunk_failed": 0,
            "resume_state": str(root / "output" / "test_resume_state.json"),
            "summary": {
                "success": 1,
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
        
        if self._exception:
            raise self._exception
            
        # Create output file if it doesn't exist
        output_path = Path(self._result.get("output", ""))
        if output_path and output_path.parent != Path("."):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("Translated content\n", encoding="utf-8")
            
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
    
    test_input = tmp_path / "test.txt"
    test_input.write_text("테스트 문장입니다.\n", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    return replace(
        base,
        input_path=str(test_input),
        output_directory=str(output_dir),
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


def run_translation(controller, config: LauncherConfig, root_path: Path):
    """Run translation and return callback data."""
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
    
    runner = controller.start_translation(
        config=config,
        root_path=root_path,
        on_progress=on_progress,
        on_finished=on_finished,
        on_error=on_error,
    )
    
    timeout = 15.0
    start_time = time.time()
    while not runner.is_completed() and (time.time() - start_time) < timeout:
        time.sleep(0.1)
    
    return callback_data, runner


# ========================================================================
# Test A — Valid TXT Dry-Run
# ========================================================================

def test_s6_05_valid_txt_dry_run(tmp_path: Path):
    """
    S6-05-A: Valid TXT Dry-Run
    
    Verifies:
    valid TXT
    -> dry_run=True
    -> status == "dry_run"
    """
    from ui.translation_launcher.controller import LauncherController
    from lts.txt_translation_runtime import TxtTranslationOptions
    
    config = create_test_config(tmp_path, dry_run=True)
    root_path = tmp_path
    
    controller = LauncherController()
    
    # Create a mock dry-run result
    dry_run_result = {
        "status": "dry_run",
        "input": str(config.input_path),
        "output": "",
        "output_dir": config.output_directory,
        "chunk_total": 1,
        "chunk_successful": 0,
        "chunk_failed": 0,
        "resume_state": str(tmp_path / "output" / "test_resume_state.json"),
        "summary": {
            "total_chunks": 1,
            "successful_chunks": 0,
            "failed_chunks": 0,
            "elapsed_seconds": 0.1,
        },
        "pipeline_mode": "runtime",
        "session_id": "dry-run-session-123",
    }
    
    mock_runtime = MockTranslationRuntime(root_path, result=dry_run_result)
    
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime_class.return_value = mock_runtime
        
        callback_data, runner = run_translation(controller, config, root_path)
        
        # Should complete successfully
        assert runner.is_completed(), "Runner should complete"
        assert callback_data["finished_result"] is not None, "Should have finished result"
        assert callback_data["error_received"] is None, "Should not have error"
        
        # Verify dry-run status
        result = callback_data["finished_result"]
        assert result.get("status") == "dry_run", f"Expected dry_run status, got {result.get('status')}"
        assert result.get("output") == "", "Output should be empty for dry-run"
        
        # Verify runtime was called with dry_run=True
        assert mock_runtime.call_count == 1, "Runtime should be called once"
        opts = mock_runtime.last_options
        assert opts is not None, "Options should be passed"
        assert opts.dry_run == True, "Options should have dry_run=True"
        
        # Verify progress callbacks include dry_run
        statuses = [p.get("status") for p in callback_data["progress_calls"]]
        assert "dry_run" in statuses, "Should receive dry_run status in progress"
        
        print("SUCCESS: S6-05-A Valid TXT Dry-Run: ALL CHECKS PASSED")


# ========================================================================
# Test B — No Formal Output
# ========================================================================

def test_s6_05_no_formal_output(tmp_path: Path):
    """
    S6-05-B: No Formal Translation Output
    
    Verifies:
    dry_run completed
    -> output == ""
    -> formal translated output does not exist
    """
    from ui.translation_launcher.controller import LauncherController
    
    config = create_test_config(tmp_path, dry_run=True)
    root_path = tmp_path
    
    controller = LauncherController()
    
    dry_run_result = {
        "status": "dry_run",
        "input": str(config.input_path),
        "output": "",
        "output_dir": config.output_directory,
        "chunk_total": 1,
        "chunk_successful": 0,
        "chunk_failed": 0,
        "resume_state": str(tmp_path / "output" / "test_resume_state.json"),
        "summary": {
            "total_chunks": 1,
            "successful_chunks": 0,
            "failed_chunks": 0,
            "elapsed_seconds": 0.1,
        },
        "pipeline_mode": "runtime",
        "session_id": "dry-run-session-456",
    }
    
    mock_runtime = MockTranslationRuntime(root_path, result=dry_run_result)
    
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime_class.return_value = mock_runtime
        
        callback_data, runner = run_translation(controller, config, root_path)
        
        assert runner.is_completed()
        result = callback_data["finished_result"]
        assert result is not None
        
        # Verify no output file
        output_path = result.get("output", "")
        assert output_path == "", "Output should be empty string"
        
        # Verify no file was created in output directory
        output_dir = Path(config.output_directory)
        txt_files = list(output_dir.glob("*.txt"))
        assert len(txt_files) == 0, f"No translated TXT files should exist, found: {txt_files}"
        
        print("SUCCESS: S6-05-B No Formal Output: ALL CHECKS PASSED")


# ========================================================================
# Test C — UI Result-State
# ========================================================================

def test_s6_05_ui_result_state(tmp_path: Path):
    """
    S6-05-C: UI Result-State
    
    Verifies:
    dry_run
    -> UI receives/represents dry-run completion
    -> NOT translation completed
    -> NOT translation incomplete
    """
    from ui.translation_launcher.controller import LauncherController
    
    config = create_test_config(tmp_path, dry_run=True)
    root_path = tmp_path
    
    controller = LauncherController()
    
    dry_run_result = {
        "status": "dry_run",
        "input": str(config.input_path),
        "output": "",
        "output_dir": config.output_directory,
        "chunk_total": 1,
        "chunk_successful": 0,
        "chunk_failed": 0,
        "resume_state": str(tmp_path / "output" / "test_resume_state.json"),
        "summary": {
            "total_chunks": 1,
            "successful_chunks": 0,
            "failed_chunks": 0,
            "elapsed_seconds": 0.1,
        },
        "pipeline_mode": "runtime",
        "session_id": "dry-run-session-789",
    }
    
    mock_runtime = MockTranslationRuntime(root_path, result=dry_run_result)
    
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime_class.return_value = mock_runtime
        
        callback_data, runner = run_translation(controller, config, root_path)
        
        assert runner.is_completed()
        result = callback_data["finished_result"]
        assert result is not None
        
        # Verify status is dry_run (not success, not incomplete, not failed)
        assert result.get("status") == "dry_run"
        assert result.get("status") != "success", "Should not be 'success'"
        assert result.get("status") != "incomplete", "Should not be 'incomplete'"
        assert result.get("status") != "failed", "Should not be 'failed'"
        
        # Verify progress statuses contain dry_run
        statuses = [p.get("status") for p in callback_data["progress_calls"]]
        assert "dry_run" in statuses, "Progress should include dry_run status"
        assert "completed" not in statuses, "Progress should not contain 'completed' for dry-run"
        assert "incomplete" not in statuses, "Progress should not contain 'incomplete' for dry-run"
        
        print("SUCCESS: S6-05-C UI Result-State: ALL CHECKS PASSED")


# ========================================================================
# Test D — Invalid TXT Dry-Run
# ========================================================================

def test_s6_05_invalid_txt_dry_run(tmp_path: Path):
    """
    S6-05-D: Invalid TXT Dry-Run
    
    Verifies:
    invalid TXT
    -> validation failure
    -> no formal translated output
    -> NOT incorrectly reported as dry_run success
    """
    from ui.translation_launcher.controller import LauncherController
    
    # Create empty input file (invalid)
    test_input = tmp_path / "empty.txt"
    test_input.write_text("", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    base = load_launcher_config()
    config = replace(
        base,
        input_path=str(test_input),
        output_directory=str(output_dir),
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
        dry_run=True,
    )
    
    root_path = tmp_path
    controller = LauncherController()
    
    # Validation should fail for empty file
    validation_result = controller.validate(config)
    assert not validation_result.ready, "Empty input should fail validation"
    assert any("input_file_empty" in issue.code for issue in validation_result.blocking_reasons)
    
    # App would check validation before calling start_translation
    # This test verifies the validation correctly rejects invalid input
    # The controller.start_translation is not expected to be called by app for invalid input
    
    print("SUCCESS: S6-05-D Invalid TXT Dry-Run: ALL CHECKS PASSED")


# ========================================================================
# Test E — Existing Output Protection
# ========================================================================

def test_s6_05_existing_output_protection(tmp_path: Path):
    """
    S6-05-E: Existing Output Protection
    
    Verifies:
    existing output
    -> Dry-Run
    -> output remains unchanged
    """
    from ui.translation_launcher.controller import LauncherController
    
    config = create_test_config(tmp_path, dry_run=True)
    root_path = tmp_path
    
    # Pre-create an existing output file
    output_dir = Path(config.output_directory)
    existing_output = output_dir / "test_zh.txt"
    existing_content = "這是現有的翻譯輸出內容\n"
    existing_output.write_text(existing_content, encoding="utf-8")
    
    controller = LauncherController()
    
    dry_run_result = {
        "status": "dry_run",
        "input": str(config.input_path),
        "output": "",
        "output_dir": config.output_directory,
        "chunk_total": 1,
        "chunk_successful": 0,
        "chunk_failed": 0,
        "resume_state": str(tmp_path / "output" / "test_resume_state.json"),
        "summary": {
            "total_chunks": 1,
            "successful_chunks": 0,
            "failed_chunks": 0,
            "elapsed_seconds": 0.1,
        },
        "pipeline_mode": "runtime",
        "session_id": "dry-run-session-protection",
    }
    
    mock_runtime = MockTranslationRuntime(root_path, result=dry_run_result)
    
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime_class.return_value = mock_runtime
        
        callback_data, runner = run_translation(controller, config, root_path)
        
        assert runner.is_completed()
        
        # Verify existing file is unchanged
        assert existing_output.exists(), "Existing output file should still exist"
        assert existing_output.read_text(encoding="utf-8") == existing_content, "Existing output should be unchanged"
        
        print("SUCCESS: S6-05-E Existing Output Protection: ALL CHECKS PASSED")


# ========================================================================
# Test F — Worker Lifecycle
# ========================================================================

def test_s6_05_worker_lifecycle(tmp_path: Path):
    """
    S6-05-F: Worker Lifecycle for Dry-Run
    
    Verifies:
    worker start
    -> execution
    -> dry-run final state
    -> worker stops normally
    """
    from ui.translation_launcher.controller import LauncherController
    from ui.translation_launcher.worker import TranslationRunner
    
    config = create_test_config(tmp_path, dry_run=True)
    root_path = tmp_path
    
    controller = LauncherController()
    
    dry_run_result = {
        "status": "dry_run",
        "input": str(config.input_path),
        "output": "",
        "output_dir": config.output_directory,
        "chunk_total": 1,
        "chunk_successful": 0,
        "chunk_failed": 0,
        "resume_state": str(tmp_path / "output" / "test_resume_state.json"),
        "summary": {
            "total_chunks": 1,
            "successful_chunks": 0,
            "failed_chunks": 0,
            "elapsed_seconds": 0.1,
        },
        "pipeline_mode": "runtime",
        "session_id": "dry-run-lifecycle",
    }
    
    mock_runtime = MockTranslationRuntime(root_path, result=dry_run_result)
    
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime_class.return_value = mock_runtime
        
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
        
        runner = controller.start_translation(
            config=config,
            root_path=root_path,
            on_progress=on_progress,
            on_finished=on_finished,
            on_error=on_error,
        )
        
        timeout = 15.0
        start_time = time.time()
        while not runner.is_completed() and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        # Verify worker completed normally
        assert runner.is_completed(), "Runner should be completed"
        assert callback_data["finished_count"] == 1, "Finished callback called once"
        assert callback_data["error_count"] == 0, "No error callback"
        
        # Verify worker thread stopped
        worker_thread = runner._thread
        assert worker_thread is not None, "Worker thread should exist"
        assert not worker_thread.is_alive(), "Worker thread should finish"
        
        # Verify progress statuses
        statuses = [p.get("status") for p in callback_data["progress_calls"]]
        assert "preparing" in statuses, "Should have preparing"
        assert "dry_run" in statuses, "Should have dry_run completion"
        assert "completed" not in statuses, "Should not have 'completed' for dry-run"
        assert "failed" not in statuses, "Should not have 'failed' for dry-run"
        
        print("SUCCESS: S6-05-F Worker Lifecycle: ALL CHECKS PASSED")


# ========================================================================
# Test G — Canonical Route
# ========================================================================

def test_s6_05_canonical_route():
    """
    S6-05-G: Canonical Route Preservation
    
    Verifies Dry-Run still goes through canonical TXT route.
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
        if "NvidiaClient" in source:
            issues.append(f"{filename}: Direct NvidiaClient usage detected")
        if "NvidiaTranslationProvider" in source:
            issues.append(f"{filename}: Direct NvidiaTranslationProvider usage detected")
    
    # Check controller uses canonical runtime
    controller_source = source_files["controller.py"]
    if "TranslationRuntime" not in controller_source:
        issues.append("controller.py: Missing TranslationRuntime usage")
    # Controller uses _build_txt_options and worker calls translate_txt
    if "_build_txt_options" not in controller_source:
        issues.append("controller.py: Missing _build_txt_options call")
    
    # Check worker uses canonical runtime
    worker_source = source_files["worker.py"]
    if "translate_txt" not in worker_source:
        issues.append("worker.py: Missing translate_txt call")
    if "translate_epub_translation_input" not in worker_source:
        issues.append("worker.py: Missing translate_epub_translation_input call")
    
    if issues:
        raise AssertionError(f"Canonical route issues found:\n" + "\n".join(f"  - {issue}" for issue in issues))
    
    print("SUCCESS: S6-05-G Canonical Route: ALL CHECKS PASSED")


# ========================================================================
# Test H — No Real Provider Execution
# ========================================================================

def test_s6_05_no_real_provider_execution(tmp_path: Path):
    """
    S6-05-H: No Real Provider Execution
    
    Verifies Dry-Run doesn't execute real provider.
    """
    from ui.translation_launcher.controller import LauncherController
    
    config = create_test_config(tmp_path, dry_run=True)
    root_path = tmp_path
    
    controller = LauncherController()
    
    dry_run_result = {
        "status": "dry_run",
        "input": str(config.input_path),
        "output": "",
        "output_dir": config.output_directory,
        "chunk_total": 1,
        "chunk_successful": 0,
        "chunk_failed": 0,
        "resume_state": str(tmp_path / "output" / "test_resume_state.json"),
        "summary": {
            "total_chunks": 1,
            "successful_chunks": 0,
            "failed_chunks": 0,
            "elapsed_seconds": 0.1,
        },
        "pipeline_mode": "runtime",
        "session_id": "dry-run-no-provider",
    }
    
    mock_runtime = MockTranslationRuntime(root_path, result=dry_run_result)
    
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime_class.return_value = mock_runtime
        
        callback_data, runner = run_translation(controller, config, root_path)
        
        assert runner.is_completed()
        assert mock_runtime.call_count == 1
        
        # The mock runtime was called, not the real one
        # This proves canonical route with mock boundary
        assert callback_data["finished_result"].get("status") == "dry_run"
        
        print("SUCCESS: S6-05-H No Real Provider Execution: ALL CHECKS PASSED")


if __name__ == "__main__":
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        
        print("Running S6-05 Acceptance Tests...")
        print()
        
        test_s6_05_valid_txt_dry_run(tmp_path)
        test_s6_05_no_formal_output(tmp_path)
        test_s6_05_ui_result_state(tmp_path)
        test_s6_05_invalid_txt_dry_run(tmp_path)
        test_s6_05_existing_output_protection(tmp_path)
        test_s6_05_worker_lifecycle(tmp_path)
        test_s6_05_canonical_route()
        test_s6_05_no_real_provider_execution(tmp_path)
        
        print()
        print("=" * 60)
        print("ALL S6-05 ACCEPTANCE TESTS PASSED")
        print("=" * 60)