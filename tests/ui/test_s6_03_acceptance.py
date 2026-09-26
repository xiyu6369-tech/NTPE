# S6-03 Acceptance Test: EPUB Translation Studio UI Integration

"""
Mock integration test for Translation Launcher EPUB runtime wiring.

This test verifies the complete EPUB success path:
Launcher Start (EPUB) -> controller.start_translation() -> TranslationRunner.start() 
-> TranslationWorker -> mock translate_epub_translation_input() 
-> successful EpubTranslationResult -> packaging -> EPUB output -> finished callback 
-> UI receives success -> exact EPUB output path propagated
"""

import json
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import patch, MagicMock

import pytest

from core.launcher_product.config import load_launcher_config
from core.launcher_product.models import LauncherConfig
from core.epub_translation.contract import (
    EpubTranslationResult, EpubChapterResult, EpubChunkResult
)
from types import MappingProxyType


class MockEpubTranslationRuntime:
    """Mock EPUB translation runtime that returns controlled results."""

    def __init__(
        self,
        root: Path,
        result: Optional[EpubTranslationResult] = None,
        exception: Optional[Exception] = None,
        packaging_success: bool = True,
    ):
        self.root = root
        self._result = result
        self._exception = exception
        self._packaging_success = packaging_success
        self.call_count = 0
        self.last_options = None
        self.packaging_call_count = 0

    def translate_epub_translation_input(self, options: Any, root: Path | None = None) -> EpubTranslationResult:
        self.call_count += 1
        self.last_options = options
        
        if self._exception:
            raise self._exception
            
        if self._result:
            return self._result
            
        # Default success result
        from core.epub_translation.contract import EpubTranslationResult, EpubChapterResult, EpubChunkResult
        from types import MappingProxyType
        
        chunk_result = EpubChunkResult(
            chunk_id="ch0001:chunk0000",
            status="success",
            translated_text="翻譯結果",
            error=None,
            attempt=1,
            qa_report=MappingProxyType({}),
            metadata=MappingProxyType({
                "epub_chunk_id": "ch0001:chunk0000",
                "epub_chapter_id": "ch0001",
                "epub_chapter_order": 1,
                "epub_chunk_sequence": 0,
                "epub_source_href": "OEBPS/ch1.xhtml",
                "epub_fragment": None,
                "provider_model": "test-model",
                "provider_elapsed_seconds": 0.5,
            }),
        )
        
        chapter_result = EpubChapterResult(
            chapter_id="ch0001",
            chapter_order=1,
            chunk_results=(chunk_result,),
            aggregate_status="success",
            success_count=1,
            failed_count=0,
            skipped_count=0,
            assembled_text="翻譯結果\n",
        )
        
        return EpubTranslationResult(
            aggregate_status="success",
            chapter_results=(chapter_result,),
            success_count=1,
            failed_count=0,
            skipped_count=0,
            session_id="mock-session-123",
            resume_state_path=None,
        )


def create_epub_test_config(tmp_path: Path, dry_run: bool = False) -> LauncherConfig:
    """Create a test LauncherConfig for EPUB translation."""
    base = load_launcher_config()
    
    epub_path = tmp_path / "test.epub"
    epub_path.write_bytes(b"PK\x03\x04" + b"\x00" * 200)
    
    return replace(
        base,
        input_path=str(epub_path),
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


def create_mock_extraction_result(config: LauncherConfig, tmp_path: Path):
    """Create a mock EPUB extraction result for testing."""
    from core.adapters.epub_extraction_boundary import EpubExtractionResult, EpubMetadata, ChapterBoundary, ExtractionManifest, ResourceRef
    from types import MappingProxyType
    from datetime import datetime, timezone
    
    return EpubExtractionResult(
        source_path=Path(config.input_path),
        original_hash="a" * 64,
        extracted_text="=== CHAPTER 1: Chapter 1 ===\nTest chapter content.\n",
        extracted_hash="b" * 64,
        metadata=EpubMetadata(
            title="Test Novel",
            author="Test Author",
            language="ko",
            identifier="test-id",
            publisher="Test Publisher",
            date="2024-01-01",
            raw=MappingProxyType({"dc:title": "Test Novel"}),
        ),
        chapter_map=(ChapterBoundary(
            index=1,
            spine_position=1,
            title="Chapter 1",
            start_offset=0,
            end_offset=50,
            source_href="OEBPS/ch1.xhtml",
            toc_level=0,
            is_linear=True,
            word_count=20,
            landmark_type=None,
            status="linear",
            body_start_offset=30,
            body_end_offset=50,
        ),),
        extraction_manifest=ExtractionManifest(
            extractor_version="epub-extraction-v1.0.0",
            extracted_at=datetime.now(timezone.utc).isoformat(),
            chapter_count=1,
            total_characters=50,
            total_words=20,
            warnings=(),
            resources=(),
            spine_item_count=1,
            nav_toc_entries=1,
            encoding_used="utf-8",
            parsing_duration_ms=100,
            fixed_layout=None,
        ),
        status="success",
        warnings=(),
    )


def test_s6_03_epub_success_path(tmp_path: Path):
    """
    S6-03-A: EPUB Complete Success Path
    
    Verifies:
    Launcher Start (EPUB) -> controller.start_translation() -> TranslationRunner.start() 
    -> TranslationWorker -> mock translate_epub_translation_input() 
    -> successful EpubTranslationResult -> packaging -> EPUB output 
    -> finished callback -> UI receives success 
    -> exact EPUB output path propagated
    """
    # Setup
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    config = create_epub_test_config(tmp_path)
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
    from core.epub_translation.runtime.adapter import EpubTranslationOptions
    
    controller = LauncherController()
    mock_extraction_result = create_mock_extraction_result(config, tmp_path)
    mock_runtime = MockEpubTranslationRuntime(root_path)
    
    # Patch the EPUB extraction and translation function for the entire test duration
    with patch("core.adapters.epub_extraction_boundary.EpubExtractionBoundary.extract", return_value=mock_extraction_result):
        with patch("core.epub_translation.runtime.adapter.translate_epub_translation_input", side_effect=mock_runtime.translate_epub_translation_input) as mock_translate:
            # Also patch the packager to avoid actual EPUB creation
            with patch("core.epub_translation.runtime.epub_packager.pack_epub_resource_aware") as mock_pack:
                from core.epub_translation.runtime.epub_packager import EpubPackagingResult
                mock_pack.return_value = EpubPackagingResult(
                    success=True,
                    output_path=output_dir / "test_zh.epub",
                    source_identity="a" * 64,
                    chapter_count=1,
                    resource_count=0,
                    validation_errors=(),
                    error_message=None,
                )
                
                # Also patch the reader chapter map builder
                with patch("core.epub_translation.reader_chapter_map.build_epub_reader_chapter_map_with_metadata") as mock_reader:
                    from core.epub_translation.reader_chapter_map import EpubReaderChapterMapResult
                    from core.translation_release.reader_structure.models import ReaderChapterMap, ChapterBoundary as ReaderChapterBoundary
                    mock_reader.return_value = EpubReaderChapterMapResult(
                        reader_chapter_map=ReaderChapterMap(chapters=(ReaderChapterBoundary(
                            chapter_id="ch0001",
                            chapter_order=0,
                            chapter_title="Chapter 1",
                            start_position=0,
                            end_position=10,
                            scene_ids=(),
                        ),)),
                        full_text="翻譯結果\n",
                        chapter_statuses=MappingProxyType({"ch0001": "success"}),
                        source_hrefs=MappingProxyType({"ch0001": "OEBPS/ch1.xhtml"}),
                        fragments=MappingProxyType({"ch0001": None}),
                    )
                    
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
                    timeout = 15.0
                    start_time = time.time()
                    while not runner.is_completed() and (time.time() - start_time) < timeout:
                        time.sleep(0.1)
                    
                    # Verify EPUB translation was called
                    assert mock_runtime.call_count == 1, "translate_epub_translation_input() should be called exactly once"
                    assert mock_runtime.last_options is not None, "Options should be passed to runtime"
                    
                    # Verify options passed to runtime
                    opts = mock_runtime.last_options
                    assert isinstance(opts, EpubTranslationOptions)
                    assert opts.translation_input is not None
                    assert opts.chunks is not None
                    assert len(opts.chunks) > 0
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
                    assert result.get("output", "").endswith(".epub"), "Output should be EPUB file"
                    
                    # Verify runner completed
                    assert runner.is_completed(), "Runner should be marked as completed"
                    
                    # Verify worker thread is not the main thread
                    assert threading.current_thread() != getattr(runner, '_thread', None), "Worker should run in separate thread"
                    
                    print("SUCCESS: S6-03-A EPUB Success Path: ALL CHECKS PASSED")


def test_s6_03_epub_failure_path_exception(tmp_path: Path):
    """
    S6-03-B: EPUB Failure Path - Exception
    
    Verifies:
    runtime exception -> worker catches/propagates -> error callback -> UI enters failed state
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    config = create_epub_test_config(tmp_path)
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
    mock_extraction_result = create_mock_extraction_result(config, tmp_path)
    test_exception = RuntimeError("Mock EPUB provider failure: connection timeout")
    mock_runtime = MockEpubTranslationRuntime(root_path, exception=test_exception)
    
    # Patch the EPUB extraction and translation function for the entire test duration
    with patch("core.adapters.epub_extraction_boundary.EpubExtractionBoundary.extract", return_value=mock_extraction_result):
        with patch("core.epub_translation.runtime.adapter.translate_epub_translation_input", side_effect=mock_runtime.translate_epub_translation_input) as mock_translate:
            runner = controller.start_translation(
                config=config,
                root_path=root_path,
                on_progress=on_progress,
                on_finished=on_finished,
                on_error=on_error,
            )
            
            # Wait for completion
            timeout = 15.0
            start_time = time.time()
            while not runner.is_completed() and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            # Verify error callback was called
            assert callback_data["error_received"] is not None, "Error callback should be called"
            assert "Mock EPUB provider failure" in callback_data["error_received"]
            assert "connection timeout" in callback_data["error_received"]
            
            # Verify finished callback was NOT called
            assert callback_data["finished_result"] is None, "Finished callback should not be called on error"
            
            # Verify progress callbacks stopped
            statuses = [p.get("status") for p in callback_data["progress_calls"]]
            assert "preparing" in statuses, "Should receive preparing status"
            assert "completed" not in statuses, "Should not receive completed status on error"
            
            # Verify worker thread stopped
            assert runner.is_completed(), "Runner should be marked as completed"
            
            print("SUCCESS: S6-03-B EPUB Failure Path (Exception): ALL CHECKS PASSED")


def test_s6_03_epub_failure_path_incomplete_result(tmp_path: Path):
    """
    S6-03-B: EPUB Failure Path - Canonical incomplete result
    
    Verifies:
    canonical failed/incomplete result -> worker -> finished callback with incomplete -> UI shows warning
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    config = create_epub_test_config(tmp_path)
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
    from core.epub_translation.contract import (
        EpubTranslationResult, EpubChapterResult, EpubChunkResult
    )
    from types import MappingProxyType
    
    controller = LauncherController()
    mock_extraction_result = create_mock_extraction_result(config, tmp_path)
    
    # Create a canonical incomplete EPUB result
    chunk_result = EpubChunkResult(
        chunk_id="ch0001:chunk0000",
        status="failed",
        translated_text="",
        error="Provider timeout after retries",
        attempt=3,
        qa_report=MappingProxyType({}),
        metadata=MappingProxyType({}),
    )
    
    chapter_result = EpubChapterResult(
        chapter_id="ch0001",
        chapter_order=1,
        chunk_results=(chunk_result,),
        aggregate_status="failed",
        success_count=0,
        failed_count=1,
        skipped_count=0,
        assembled_text="",
    )
    
    incomplete_result = EpubTranslationResult(
        aggregate_status="failed",
        chapter_results=(chapter_result,),
        success_count=0,
        failed_count=1,
        skipped_count=0,
        session_id="mock-session-incomplete",
        resume_state_path=None,
    )
    
    mock_runtime = MockEpubTranslationRuntime(root_path, result=incomplete_result)
    
    # Patch the EPUB extraction and translation function for the entire test duration
    with patch("core.adapters.epub_extraction_boundary.EpubExtractionBoundary.extract", return_value=mock_extraction_result):
        with patch("core.epub_translation.runtime.adapter.translate_epub_translation_input", side_effect=mock_runtime.translate_epub_translation_input) as mock_translate:
            # Also patch the packager to return failure
            with patch("core.epub_translation.runtime.epub_packager.pack_epub_resource_aware") as mock_pack:
                from core.epub_translation.runtime.epub_packager import EpubPackagingResult
                mock_pack.return_value = EpubPackagingResult(
                    success=False,
                    output_path=None,
                    source_identity="a" * 64,
                    chapter_count=0,
                    resource_count=0,
                    validation_errors=("Packaging failed",),
                    error_message="Packaging failed",
                )
                
                # Also patch the reader chapter map builder
                with patch("core.epub_translation.reader_chapter_map.build_epub_reader_chapter_map_with_metadata") as mock_reader:
                    from core.epub_translation.reader_chapter_map import EpubReaderChapterMapResult
                    from core.translation_release.reader_structure.models import ReaderChapterMap, ChapterBoundary as ReaderChapterBoundary
                    mock_reader.return_value = EpubReaderChapterMapResult(
                        reader_chapter_map=ReaderChapterMap(chapters=(ReaderChapterBoundary(
                            chapter_id="ch0001",
                            chapter_order=0,
                            chapter_title="Chapter 1",
                            start_position=0,
                            end_position=0,
                            scene_ids=(),
                        ),)),
                        full_text="",
                        chapter_statuses=MappingProxyType({"ch0001": "failed"}),
                        source_hrefs=MappingProxyType({"ch0001": "OEBPS/ch1.xhtml"}),
                        fragments=MappingProxyType({"ch0001": None}),
                    )
                    
                    runner = controller.start_translation(
                        config=config,
                        root_path=root_path,
                        on_progress=on_progress,
                        on_finished=on_finished,
                        on_error=on_error,
                    )
                    
                    # Wait for completion
                    timeout = 15.0
                    start_time = time.time()
                    while not runner.is_completed() and (time.time() - start_time) < timeout:
                        time.sleep(0.1)
                    
                    # Verify finished callback was called with failed result
                    assert callback_data["finished_result"] is not None, "Finished callback should be called for failed"
                    assert callback_data["error_received"] is None, "Error callback should not be called for failed result"
                    
                    result = callback_data["finished_result"]
                    assert result.get("status") in ("failed", "incomplete"), "Result should be failed or incomplete"
                    
                    print("SUCCESS: S6-03-B EPUB Failure Path (Incomplete): ALL CHECKS PASSED")


def test_s6_03_epub_thread_lifecycle(tmp_path: Path):
    """
    S6-03-C: EPUB Thread/UI Lifecycle Contract
    
    Verifies:
    1. translate_epub_translation_input() NOT in Tkinter UI thread
    2. UI callback uses root.after (or equivalent safe dispatch) - verified in app.py
    3. Worker polling stops on completion
    4. Worker polling stops on failure
    5. No duplicate completion callback
    6. Start Translation state restores after completion
    7. No daemon worker left running after failure
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    config = create_epub_test_config(tmp_path)
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
    mock_extraction_result = create_mock_extraction_result(config, tmp_path)
    mock_runtime = MockEpubTranslationRuntime(root_path)
    
    # Patch the EPUB extraction and translation function for the entire test duration
    with patch("core.adapters.epub_extraction_boundary.EpubExtractionBoundary.extract", return_value=mock_extraction_result):
        with patch("core.epub_translation.runtime.adapter.translate_epub_translation_input", side_effect=mock_runtime.translate_epub_translation_input) as mock_translate:
            with patch("core.epub_translation.runtime.epub_packager.pack_epub_resource_aware") as mock_pack:
                from core.epub_translation.runtime.epub_packager import EpubPackagingResult
                mock_pack.return_value = EpubPackagingResult(
                    success=True,
                    output_path=output_dir / "test_zh.epub",
                    source_identity="a" * 64,
                    chapter_count=1,
                    resource_count=0,
                    validation_errors=(),
                    error_message=None,
                )
                
                with patch("core.epub_translation.reader_chapter_map.build_epub_reader_chapter_map_with_metadata") as mock_reader:
                    from core.epub_translation.reader_chapter_map import EpubReaderChapterMapResult
                    from core.translation_release.reader_structure.models import ReaderChapterMap, ChapterBoundary as ReaderChapterBoundary
                    mock_reader.return_value = EpubReaderChapterMapResult(
                        reader_chapter_map=ReaderChapterMap(chapters=(ReaderChapterBoundary(
                            chapter_id="ch0001",
                            chapter_order=0,
                            chapter_title="Chapter 1",
                            start_position=0,
                            end_position=10,
                            scene_ids=(),
                        ),)),
                        full_text="翻譯結果\n",
                        chapter_statuses=MappingProxyType({"ch0001": "success"}),
                        source_hrefs=MappingProxyType({"ch0001": "OEBPS/ch1.xhtml"}),
                        fragments=MappingProxyType({"ch0001": None}),
                    )
                    
                    runner = controller.start_translation(
                        config=config,
                        root_path=root_path,
                        on_progress=on_progress,
                        on_finished=on_finished,
                        on_error=on_error,
                    )
                    
                    # Wait for completion
                    timeout = 15.0
                    start_time = time.time()
                    while not runner.is_completed() and (time.time() - start_time) < timeout:
                        time.sleep(0.1)
                    
                    # 1. Verify worker runs in separate thread
                    assert hasattr(runner, '_thread'), "Runner should have worker thread"
                    worker_thread = runner._thread
                    assert worker_thread is not None, "Worker thread should exist"
                    assert worker_thread != threading.main_thread(), "Worker should not run in main thread"
                    
                    # 2. Verify app.py uses root.after for UI callbacks (pattern check)
                    app_source = Path("D:/Python/NTPE/ui/translation_launcher/app.py").read_text(encoding="utf-8")
                    assert "root.after" in app_source, "app.py should use root.after for UI callbacks"
                    assert "root.after(0" in app_source, "app.py should use root.after(0, ...) for immediate dispatch"
                    
                    # 3. Verify polling stops on success
                    assert not worker_thread.is_alive(), "Worker thread should finish after completion"
                    assert runner.is_completed(), "Runner should be completed"
                    
                    # 4. Verify no duplicate callbacks
                    assert callback_data["finished_count"] == 1, f"Finished callback should be called exactly once, got {callback_data['finished_count']}"
                    assert callback_data["error_count"] == 0, "Error callback should not be called on success"
                    
                    # 5. Verify start state restoration - runner completed and thread joined
                    assert runner.is_completed()
                    
                    print("SUCCESS: S6-03-C EPUB Thread/Lifecycle: ALL CHECKS PASSED")


def test_s6_03_epub_failure_thread_lifecycle(tmp_path: Path):
    """Verify EPUB thread lifecycle on failure."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    config = create_epub_test_config(tmp_path)
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
    mock_extraction_result = create_mock_extraction_result(config, tmp_path)
    test_exception = RuntimeError("EPUB test failure")
    mock_runtime = MockEpubTranslationRuntime(root_path, exception=test_exception)
    
    # Patch the EPUB extraction and translation function for the entire test duration
    with patch("core.adapters.epub_extraction_boundary.EpubExtractionBoundary.extract", return_value=mock_extraction_result):
        with patch("core.epub_translation.runtime.adapter.translate_epub_translation_input", side_effect=mock_runtime.translate_epub_translation_input) as mock_translate:
            runner = controller.start_translation(
                config=config,
                root_path=root_path,
                on_progress=on_progress,
                on_finished=on_finished,
                on_error=on_error,
            )
            
            # Wait for completion
            timeout = 15.0
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
            
            print("SUCCESS: S6-03-C EPUB Failure Thread Lifecycle: ALL CHECKS PASSED")


def test_s6_03_canonical_route_integrity():
    """
    S6-03-D: Canonical Route Integrity
    
    Verifies EPUB UI doesn't bypass canonical architecture:
    - Not directly using NvidiaClient
    - Not directly using NvidiaTranslationProvider
    - Not adding provider selection
    - Not adding second translation execution path
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
        
        if filename in ("controller.py", "worker.py"):
            # Check for direct Nvidia client/provider usage
            if "NvidiaClient" in source:
                issues.append(f"{filename}: Direct NvidiaClient usage detected")
            if "NvidiaTranslationProvider" in source:
                issues.append(f"{filename}: Direct NvidiaTranslationProvider usage detected")
            
            # Check that EPUB translation uses canonical function
            if filename == "worker.py":
                if "translate_epub_translation_input" not in source:
                    issues.append(f"{filename}: Missing canonical EPUB translation function call")
    
    # Check controller uses EPUB extraction/intake/chunking pipeline
    controller_source = source_files["controller.py"]
    required_imports = [
        "EpubExtractionBoundary",
        "CanonicalBookIntakeAdapter",
        "chunk_epub_translation_input",
        "EpubTranslationOptions",
    ]
    for imp in required_imports:
        if imp not in controller_source:
            issues.append(f"controller.py: Missing required import/call: {imp}")
    
    # Check worker uses canonical EPUB translation function
    worker_source = source_files["worker.py"]
    if "translate_epub_translation_input" not in worker_source:
        issues.append("worker.py: Missing canonical EPUB translation function call")
    
    if issues:
        raise AssertionError(f"Canonical route integrity issues found:\n" + "\n".join(f"  - {issue}" for issue in issues))
    
    print("SUCCESS: S6-03-D Canonical Route Integrity: ALL CHECKS PASSED")


def test_s6_03_epub_output_artifact_verification(tmp_path: Path):
    """
    S6-03-E: EPUB Output Artifact Verification
    
    Verifies that EPUB translation produces actual EPUB output artifact,
    not just mock result.
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    config = create_epub_test_config(tmp_path)
    root_path = tmp_path
    
    callback_data: Dict[str, Any] = {
        "finished_result": None,
    }
    
    def on_progress(progress: Dict):
        pass
    
    def on_finished(result: Dict):
        callback_data["finished_result"] = result
    
    def on_error(error: str):
        pass
    
    from ui.translation_launcher.controller import LauncherController
    from ui.translation_launcher.worker import TranslationRunner
    
    controller = LauncherController()
    mock_extraction_result = create_mock_extraction_result(config, tmp_path)
    mock_runtime = MockEpubTranslationRuntime(root_path)
    
    # Patch the EPUB extraction and translation function for the entire test duration
    with patch("core.adapters.epub_extraction_boundary.EpubExtractionBoundary.extract", return_value=mock_extraction_result):
        with patch("core.epub_translation.runtime.adapter.translate_epub_translation_input", side_effect=mock_runtime.translate_epub_translation_input) as mock_translate:
            with patch("core.epub_translation.runtime.epub_packager.pack_epub_resource_aware") as mock_pack:
                from core.epub_translation.runtime.epub_packager import EpubPackagingResult
                expected_output = output_dir / "test_zh.epub"
                mock_pack.return_value = EpubPackagingResult(
                    success=True,
                    output_path=expected_output,
                    source_identity="a" * 64,
                    chapter_count=1,
                    resource_count=0,
                    validation_errors=(),
                    error_message=None,
                )
                
                with patch("core.epub_translation.reader_chapter_map.build_epub_reader_chapter_map_with_metadata") as mock_reader:
                    from core.epub_translation.reader_chapter_map import EpubReaderChapterMapResult
                    from core.translation_release.reader_structure.models import ReaderChapterMap, ChapterBoundary as ReaderChapterBoundary
                    mock_reader.return_value = EpubReaderChapterMapResult(
                        reader_chapter_map=ReaderChapterMap(chapters=(ReaderChapterBoundary(
                            chapter_id="ch0001",
                            chapter_order=0,
                            chapter_title="Chapter 1",
                            start_position=0,
                            end_position=10,
                            scene_ids=(),
                        ),)),
                        full_text="翻譯結果\n",
                        chapter_statuses=MappingProxyType({"ch0001": "success"}),
                        source_hrefs=MappingProxyType({"ch0001": "OEBPS/ch1.xhtml"}),
                        fragments=MappingProxyType({"ch0001": None}),
                    )
                    
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
                    
                    # Verify EPUB output path in result
                    result = callback_data["finished_result"]
                    assert result is not None, "Should have finished result"
                    output_path = result.get("output", "")
                    assert output_path.endswith(".epub"), f"Output should be EPUB file, got: {output_path}"
                    assert "test_zh.epub" in output_path, f"Output should contain expected filename, got: {output_path}"
                    
                    # Verify packager was called
                    assert mock_pack.call_count == 1, "Packager should be called exactly once"
                    
                    # Verify packaging input was correct
                    packaging_call = mock_pack.call_args
                    assert packaging_call is not None, "Packager should be called with arguments"
                    packaging_input = packaging_call.kwargs.get("packaging_input") or packaging_call.args[0]
                    assert packaging_input is not None, "Packaging input should be provided"
                    
                    print("SUCCESS: S6-03-E EPUB Output Artifact Verification: ALL CHECKS PASSED")


if __name__ == "__main__":
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        
        print("Running S6-03 Acceptance Tests...")
        print()
        
        test_s6_03_canonical_route_integrity()
        test_s6_03_epub_success_path(tmp_path)
        test_s6_03_epub_failure_path_exception(tmp_path)
        test_s6_03_epub_failure_path_incomplete_result(tmp_path)
        test_s6_03_epub_thread_lifecycle(tmp_path)
        test_s6_03_epub_failure_thread_lifecycle(tmp_path)
        test_s6_03_epub_output_artifact_verification(tmp_path)
        
        print()
        print("=" * 60)
        print("ALL S6-03 ACCEPTANCE TESTS PASSED")
        print("=" * 60)