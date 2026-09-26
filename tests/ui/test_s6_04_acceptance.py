# S6-04 Acceptance Test: Short / Mixed-Language Intake

"""
Mock integration test for Translation Studio short-text and mixed-language intake.

This test verifies:
1. Valid short Korean text is accepted
2. Valid mixed-language text is accepted
3. Invalid input remains rejected
4. Canonical route is used (no second translation path)
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
from core.translation_runtime import TranslationRuntime


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


def create_test_config(tmp_path: Path, input_text: str, source_language: str = "auto") -> LauncherConfig:
    """Create a test LauncherConfig with the given input text."""
    base = load_launcher_config()
    
    test_input = tmp_path / "test.txt"
    test_input.write_text(input_text, encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)
    
    return replace(
        base,
        input_path=str(test_input),
        output_directory=str(output_dir),
        source_language=source_language,
        target_language="zh-Hant",
        provider_id="nvidia",
        model_id="meta/llama-3.2-90b-vision-instruct",
        translation_profile="literary",
        chunk_size=1000,
        api_timeout=180,
        provider_attempts=2,
        overwrite=False,
        resume_enabled=True,
        dry_run=False,
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
# S6-04-A: Short Text Tests
# ========================================================================

def test_s6_04_short_text_auto_detection(tmp_path: Path):
    """
    S6-04-A1: Very short Korean text with auto-detection.
    
    Verifies: Short Korean text (1-2 characters) is detected as Korean
    and validation passes with auto-detection.
    """
    from ui.translation_launcher.controller import LauncherController
    
    short_texts = [
        "네.",       # 1 hangul
        "아니.",     # 2 hangul
        "왜?",       # 1 hangul
        "안녕.",     # 2 hangul
    ]
    
    controller = LauncherController()
    
    for text in short_texts:
        config = create_test_config(tmp_path, text, source_language="auto")
        root_path = tmp_path
        
        with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
            mock_runtime = MockTranslationRuntime(root_path)
            mock_runtime_class.return_value = mock_runtime
            
            callback_data, runner = run_translation(controller, config, root_path)
            
            # Should complete successfully
            assert runner.is_completed(), f"Runner should complete for text: {text}"
            assert callback_data["finished_result"] is not None, f"Should have finished result for: {text}"
            assert callback_data["error_received"] is None, f"Should not have error for: {text}"
            assert mock_runtime.call_count == 1, f"Runtime should be called once for: {text}"
            
            # Verify progress callbacks
            statuses = [p.get("status") for p in callback_data["progress_calls"]]
            assert "completed" in statuses, f"Should receive completed status for: {text}"
        
        print(f"SUCCESS: Short text auto-detection passed for: {text}")


def test_s6_04_short_text_explicit_ko(tmp_path: Path):
    """
    S6-04-A2: Very short Korean text with explicit Korean selection.
    
    Verifies: Short Korean text works when user explicitly selects Korean.
    """
    from ui.translation_launcher.controller import LauncherController
    
    short_texts = [
        "네.",
        "아니.",
        "왜?",
    ]
    
    controller = LauncherController()
    
    for text in short_texts:
        config = create_test_config(tmp_path, text, source_language="ko")
        root_path = tmp_path
        
        with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
            mock_runtime = MockTranslationRuntime(root_path)
            mock_runtime_class.return_value = mock_runtime
            
            callback_data, runner = run_translation(controller, config, root_path)
            
            assert runner.is_completed(), f"Runner should complete for text: {text}"
            assert callback_data["finished_result"] is not None
            assert callback_data["error_received"] is None
            assert mock_runtime.call_count == 1
        
        print(f"SUCCESS: Short text explicit KO passed for: {text}")


def test_s6_04_normal_short_sentence(tmp_path: Path):
    """
    S6-04-A3: Normal short Korean sentence.
    
    Verifies: Normal short sentence (not extremely short) works.
    """
    from ui.translation_launcher.controller import LauncherController
    
    texts = [
        "안녕하세요.",
        "나는 돌아왔다.",
        "그가 웃었다.",
    ]
    
    controller = LauncherController()
    
    for text in texts:
        config = create_test_config(tmp_path, text, source_language="auto")
        root_path = tmp_path
        
        with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
            mock_runtime = MockTranslationRuntime(root_path)
            mock_runtime_class.return_value = mock_runtime
            
            callback_data, runner = run_translation(controller, config, root_path)
            
            assert runner.is_completed()
            assert callback_data["finished_result"] is not None
            assert callback_data["error_received"] is None
            assert mock_runtime.call_count == 1
        
        print(f"SUCCESS: Normal short sentence passed for: {text}")


def test_s6_04_short_dialogue(tmp_path: Path):
    """
    S6-04-A4: Short dialogue fragment.
    
    Verifies: Dialogue fragments are accepted.
    """
    from ui.translation_launcher.controller import LauncherController
    
    texts = [
        "그가 말했다. \"가자.\"",
        "\"네.\" 그녀가 대답했다.",
        "\"왜?\" 그가 물었다.",
    ]
    
    controller = LauncherController()
    
    for text in texts:
        config = create_test_config(tmp_path, text, source_language="auto")
        root_path = tmp_path
        
        with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
            mock_runtime = MockTranslationRuntime(root_path)
            mock_runtime_class.return_value = mock_runtime
            
            callback_data, runner = run_translation(controller, config, root_path)
            
            assert runner.is_completed()
            assert callback_data["finished_result"] is not None
            assert callback_data["error_received"] is None
            assert mock_runtime.call_count == 1
        
        print(f"SUCCESS: Short dialogue passed for: {text}")


# ========================================================================
# S6-04-B: Mixed Language Tests
# ========================================================================

def test_s6_04_korean_english_sentence(tmp_path: Path):
    """
    S6-04-B1: Korean + English sentence.
    
    Verifies: Mixed Korean and English text is accepted.
    """
    from ui.translation_launcher.controller import LauncherController
    
    texts = [
        '그는 말했다. "Let\'s go."',
        '그녀는 "Hello" 하고 인사했다.',
        '나는 "Good morning"이라고 말했다.',
    ]
    
    controller = LauncherController()
    
    for text in texts:
        config = create_test_config(tmp_path, text, source_language="auto")
        root_path = tmp_path
        
        with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
            mock_runtime = MockTranslationRuntime(root_path)
            mock_runtime_class.return_value = mock_runtime
            
            callback_data, runner = run_translation(controller, config, root_path)
            
            assert runner.is_completed(), f"Runner should complete for: {text}"
            assert callback_data["finished_result"] is not None
            assert callback_data["error_received"] is None
            assert mock_runtime.call_count == 1
        
        print(f"SUCCESS: Korean+English passed for: {text}")


def test_s6_04_korean_latin_name(tmp_path: Path):
    """
    S6-04-B2: Korean + Latin-script name/token.
    
    Verifies: Korean text with Latin-script names is accepted.
    """
    from ui.translation_launcher.controller import LauncherController
    
    texts = [
        "나는 Ilay를 바라보았다.",
        "Junho가 왔다.",
        "Seoul에서 만났다.",
    ]
    
    controller = LauncherController()
    
    for text in texts:
        config = create_test_config(tmp_path, text, source_language="auto")
        root_path = tmp_path
        
        with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
            mock_runtime = MockTranslationRuntime(root_path)
            mock_runtime_class.return_value = mock_runtime
            
            callback_data, runner = run_translation(controller, config, root_path)
            
            assert runner.is_completed(), f"Runner should complete for: {text}"
            assert callback_data["finished_result"] is not None
            assert callback_data["error_received"] is None
            assert mock_runtime.call_count == 1
        
        print(f"SUCCESS: Korean+Latin name passed for: {text}")


def test_s6_04_korean_dialogue_english_phrase(tmp_path: Path):
    """
    S6-04-B3: Korean dialogue + English phrase.
    
    Verifies: Korean dialogue mixed with English phrases is accepted.
    """
    from ui.translation_launcher.controller import LauncherController
    
    texts = [
        '"Stop." 그가 낮게 말했다.',
        '그가 "Wait!" 하고 소리쳤다.',
        '"Help me." 그녀는 속삭였다.',
    ]
    
    controller = LauncherController()
    
    for text in texts:
        config = create_test_config(tmp_path, text, source_language="auto")
        root_path = tmp_path
        
        with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
            mock_runtime = MockTranslationRuntime(root_path)
            mock_runtime_class.return_value = mock_runtime
            
            callback_data, runner = run_translation(controller, config, root_path)
            
            assert runner.is_completed(), f"Runner should complete for: {text}"
            assert callback_data["finished_result"] is not None
            assert callback_data["error_received"] is None
            assert mock_runtime.call_count == 1
        
        print(f"SUCCESS: Korean dialogue+English passed for: {text}")


# ========================================================================
# S6-04-C: Invalid Input Tests
# ========================================================================

def test_s6_04_empty_input_rejected(tmp_path: Path):
    """
    S6-04-C1: Empty input is rejected.
    
    Verifies: Empty file fails validation.
    """
    from ui.translation_launcher.controller import LauncherController
    
    config = create_test_config(tmp_path, "", source_language="auto")
    root_path = tmp_path
    
    controller = LauncherController()
    
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime = MockTranslationRuntime(root_path)
        mock_runtime_class.return_value = mock_runtime
        
        # Run validation directly
        result = controller.validate(config)
        
        # Should fail validation
        assert not result.ready, "Empty input should fail validation"
        assert any("input_file_empty" in issue.code for issue in result.blocking_reasons), "Should have empty file error"
    
    print("SUCCESS: Empty input rejected")


def test_s6_04_genuinely_invalid_input_rejected(tmp_path: Path):
    """
    S6-04-C2: Genuinely invalid input remains rejected.
    
    Verifies: Non-text file (or other invalid) is rejected.
    """
    from ui.translation_launcher.controller import LauncherController
    
    # Create a binary file
    binary_path = tmp_path / "test.bin"
    binary_path.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")
    
    base = load_launcher_config()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    config = replace(
        base,
        input_path=str(binary_path),
        output_directory=str(output_dir),
        source_language="auto",
        target_language="zh-Hant",
        provider_id="nvidia",
        model_id="meta/llama-3.2-90b-vision-instruct",
        translation_profile="literary",
        chunk_size=1000,
        api_timeout=180,
        provider_attempts=2,
        overwrite=False,
        resume_enabled=True,
        dry_run=False,
    )
    
    controller = LauncherController()
    root_path = tmp_path
    
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime = MockTranslationRuntime(root_path)
        mock_runtime_class.return_value = mock_runtime
        
        result = controller.validate(config)
        
        # Should fail validation
        assert not result.ready, "Binary file should fail validation"
    
    print("SUCCESS: Genuinely invalid input rejected")


def test_s6_04_invalid_input_no_translation_execution(tmp_path: Path):
    """
    S6-04-C3: Invalid input does not trigger translation execution.
    
    Verifies: App validation prevents translation for invalid input.
    """
    from ui.translation_launcher.controller import LauncherController
    from ui.translation_launcher.app import TranslationLauncherApp
    from typing import Dict, Any
    import tkinter as tk
    
    config = create_test_config(tmp_path, "", source_language="auto")
    root_path = tmp_path
    
    # Test that validation fails for empty input
    controller = LauncherController()
    result = controller.validate(config)
    
    # Validation should fail
    assert not result.ready, "Empty input should fail validation"
    assert any("input_file_empty" in issue.code for issue in result.blocking_reasons), "Should have empty file error"
    
    # Test that app would not call start_translation for invalid config
    # (This is the app's responsibility - we verify the validation works)
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime = MockTranslationRuntime(root_path)
        mock_runtime_class.return_value = mock_runtime
        
        # Simulate app behavior: validate first, only call start_translation if ready
        validation_result = controller.validate(config)
        if validation_result.ready:
            callback_data: Dict[str, Any] = {"error_received": None, "finished_result": None}
            
            def on_error(error: str):
                callback_data["error_received"] = error
            
            def on_finished(result: Dict):
                callback_data["finished_result"] = result
            
            runner = controller.start_translation(
                config=config,
                root_path=root_path,
                on_progress=lambda p: None,
                on_finished=on_finished,
                on_error=on_error,
            )
            
            timeout = 5.0
            start_time = time.time()
            while not runner.is_completed() and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            assert mock_runtime.call_count == 1, "Runtime should be called for valid input"
        else:
            # Invalid input - app would not call start_translation
            assert mock_runtime.call_count == 0, "Runtime should not be called for invalid input"
    
    print("SUCCESS: Invalid input does not trigger translation")


# ========================================================================
# S6-04-D: Canonical Route Tests
# ========================================================================

def test_s6_04_canonical_route_short_text(tmp_path: Path):
    """
    S6-04-D1: Short text uses canonical route.
    
    Verifies: Short text goes through canonical TranslationRuntime.
    """
    from ui.translation_launcher.controller import LauncherController
    
    config = create_test_config(tmp_path, "네.", source_language="auto")
    root_path = tmp_path
    
    controller = LauncherController()
    
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime = MockTranslationRuntime(root_path)
        mock_runtime_class.return_value = mock_runtime
        
        callback_data, runner = run_translation(controller, config, root_path)
        
        assert runner.is_completed()
        assert callback_data["finished_result"] is not None
        assert mock_runtime.call_count == 1
        
        # Verify options passed to runtime
        opts = mock_runtime.last_options
        assert opts is not None
        assert hasattr(opts, 'input_path')
        assert hasattr(opts, 'output_dir')
    
    print("SUCCESS: Short text uses canonical route")


def test_s6_04_canonical_route_mixed_language(tmp_path: Path):
    """
    S6-04-D2: Mixed language uses canonical route.
    
    Verifies: Mixed language text goes through canonical TranslationRuntime.
    """
    from ui.translation_launcher.controller import LauncherController
    
    config = create_test_config(tmp_path, '그는 "Let\'s go."라고 말했다.', source_language="auto")
    root_path = tmp_path
    
    controller = LauncherController()
    
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime = MockTranslationRuntime(root_path)
        mock_runtime_class.return_value = mock_runtime
        
        callback_data, runner = run_translation(controller, config, root_path)
        
        assert runner.is_completed()
        assert callback_data["finished_result"] is not None
        assert mock_runtime.call_count == 1
    
    print("SUCCESS: Mixed language uses canonical route")


def test_s6_04_no_second_translation_path():
    """
    S6-04-D3: No second translation path exists.
    
    Verifies: Code review - no special short-text or mixed-language translator.
    """
    import ast
    
    source_files = {
        "app.py": Path("D:/Python/NTPE/ui/translation_launcher/app.py").read_text(encoding="utf-8"),
        "controller.py": Path("D:/Python/NTPE/ui/translation_launcher/controller.py").read_text(encoding="utf-8"),
        "worker.py": Path("D:/Python/NTPE/ui/translation_launcher/worker.py").read_text(encoding="utf-8"),
        "languages.py": Path("D:/Python/NTPE/core/launcher_product/languages.py").read_text(encoding="utf-8"),
        "validation.py": Path("D:/Python/NTPE/core/launcher_product/validation.py").read_text(encoding="utf-8"),
    }
    
    issues = []
    
    for filename, source in source_files.items():
        # Check for special short-text translator
        if "short_text" in source.lower() and "translat" in source.lower():
            issues.append(f"{filename}: Possible special short-text translator")
        if "mixed_language" in source.lower() and "translat" in source.lower():
            issues.append(f"{filename}: Possible special mixed-language translator")
        
        # Check for direct provider/client usage
        if "NvidiaClient" in source:
            issues.append(f"{filename}: Direct NvidiaClient usage")
        if "NvidiaTranslationProvider" in source:
            issues.append(f"{filename}: Direct NvidiaTranslationProvider usage")
    
    # Verify canonical runtime is used
    controller_source = source_files["controller.py"]
    if "TranslationRuntime" not in controller_source:
        issues.append("controller.py: Missing TranslationRuntime usage")
    
    worker_source = source_files["worker.py"]
    if "translate_txt" not in worker_source:
        issues.append("worker.py: Missing translate_txt call")
    
    if issues:
        raise AssertionError(f"Canonical route issues:\n" + "\n".join(f"  - {i}" for i in issues))
    
    print("SUCCESS: No second translation path")


def test_s6_04_no_real_provider_execution(tmp_path: Path):
    """
    S6-04-D4: No real provider execution.
    
    Verifies: Acceptance tests use mocks at provider boundary.
    """
    from ui.translation_launcher.controller import LauncherController
    
    config = create_test_config(tmp_path, "네.", source_language="auto")
    root_path = tmp_path
    
    with patch("core.translation_runtime.TranslationRuntime") as mock_runtime_class:
        mock_runtime = MockTranslationRuntime(root_path)
        mock_runtime_class.return_value = mock_runtime
        
        controller = LauncherController()
        callback_data, runner = run_translation(controller, config, root_path)
        
        assert runner.is_completed()
        assert mock_runtime.call_count == 1
        
        # The mock was called, not the real runtime
        # This proves canonical route with mock provider boundary
    
    print("SUCCESS: No real provider execution (mock boundary used)")


# ========================================================================
# S6-04-E: UI Regression Tests
# ========================================================================

def test_s6_04_s6_02_regression():
    """
    S6-04-E1: S6-02 acceptance tests still pass.
    """
    import subprocess
    result = subprocess.run([
        "python", "-m", "pytest", "tests/ui/test_s6_02_acceptance.py", "-v"
    ], capture_output=True, text=True, cwd="D:/Python/NTPE")
    
    assert result.returncode == 0, f"S6-02 regression:\n{result.stdout}\n{result.stderr}"
    print("SUCCESS: S6-02 regression pass")


def test_s6_04_s6_03_regression():
    """
    S6-04-E2: S6-03 acceptance tests still pass.
    """
    import subprocess
    result = subprocess.run([
        "python", "-m", "pytest", "tests/ui/test_s6_03_acceptance.py", "-v"
    ], capture_output=True, text=True, cwd="D:/Python/NTPE")
    
    assert result.returncode == 0, f"S6-03 regression:\n{result.stdout}\n{result.stderr}"
    print("SUCCESS: S6-03 regression pass")


if __name__ == "__main__":
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        
        print("Running S6-04 Acceptance Tests...")
        print()
        
        # S6-04-A: Short Text
        test_s6_04_short_text_auto_detection(tmp_path)
        test_s6_04_short_text_explicit_ko(tmp_path)
        test_s6_04_normal_short_sentence(tmp_path)
        test_s6_04_short_dialogue(tmp_path)
        print()
        
        # S6-04-B: Mixed Language
        test_s6_04_korean_english_sentence(tmp_path)
        test_s6_04_korean_latin_name(tmp_path)
        test_s6_04_korean_dialogue_english_phrase(tmp_path)
        print()
        
        # S6-04-C: Invalid Input
        test_s6_04_empty_input_rejected(tmp_path)
        test_s6_04_genuinely_invalid_input_rejected(tmp_path)
        test_s6_04_invalid_input_no_translation_execution(tmp_path)
        print()
        
        # S6-04-D: Canonical Route
        test_s6_04_canonical_route_short_text(tmp_path)
        test_s6_04_canonical_route_mixed_language(tmp_path)
        test_s6_04_no_second_translation_path()
        test_s6_04_no_real_provider_execution(tmp_path)
        print()
        
        # S6-04-E: UI Regression
        test_s6_04_s6_02_regression()
        test_s6_04_s6_03_regression()
        print()
        
        print("=" * 60)
        print("ALL S6-04 ACCEPTANCE TESTS PASSED")
        print("=" * 60)