from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

from core.epub_translation.output_layout import epub_output_dir


class TranslationWorker:
    """Worker for running canonical TXT/EPUB translation in background thread (Tkinter version)."""

    def __init__(self, options: Any, root_path: Path) -> None:
        self._options = options
        self._root_path = root_path
        self._runtime = None
        self._live_progress_path: Optional[Path] = None
        self._poll_thread: Optional[threading.Thread] = None
        self._poll_running = False
        self._cancelled = False
        self._finished = False
        self._result: Optional[dict] = None
        self._error: Optional[str] = None
        self._progress_callback: Optional[Callable[[dict], None]] = None
        self._finished_callback: Optional[Callable[[dict], None]] = None
        self._error_callback: Optional[Callable[[str], None]] = None
        self._is_epub = self._detect_epub_options(options)

    def _detect_epub_options(self, options: Any) -> bool:
        """Detect if options are for EPUB translation."""
        # Check for EpubTranslationOptions type
        from core.epub_translation.runtime.adapter import EpubTranslationOptions
        return isinstance(options, EpubTranslationOptions)

    def set_callbacks(
        self,
        on_progress: Callable[[dict], None],
        on_finished: Callable[[dict], None],
        on_error: Callable[[str], None],
    ) -> None:
        self._progress_callback = on_progress
        self._finished_callback = on_finished
        self._error_callback = on_error

    def run(self) -> None:
        """Execute translation in background thread."""
        try:
            from core.translation_runtime import TranslationRuntime

            self._runtime = TranslationRuntime(root=self._root_path)

            # Determine live progress path based on input type
            if self._is_epub:
                input_stem = self._options.translation_input.source_epub_path.stem
                output_dir = epub_output_dir(
                    self._options.translation_input.source_epub_path.parent,
                    self._options.translation_input.metadata.identifier,
                )
            else:
                input_stem = self._options.input_path.stem
                output_dir = self._options.output_dir
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            self._live_progress_path = (
                output_dir
                / f"{input_stem}_live_progress.json"
            )

            if self._progress_callback:
                self._progress_callback({"status": "preparing", "message": "準備翻譯..."})

            self._poll_running = True
            self._poll_thread = threading.Thread(target=self._poll_progress, daemon=True)
            self._poll_thread.start()

            if self._is_epub:
                result = self._runtime_epub_translate(self._options)
            else:
                result = self._runtime.translate_txt(self._options)

            self._poll_running = False
            if self._poll_thread:
                self._poll_thread.join(timeout=2.0)

            self._result = result

            if self._progress_callback:
                self._emit_final_progress(result)

            if not self._cancelled and self._finished_callback:
                self._finished_callback(result)

        except Exception as e:
            self._poll_running = False
            if self._poll_thread:
                self._poll_thread.join(timeout=2.0)
            self._error = str(e)
            if not self._cancelled and self._error_callback:
                self._error_callback(str(e))
        finally:
            self._finished = True

    def _runtime_epub_translate(self, options: Any) -> dict:
        """Execute EPUB translation using canonical EPUB runtime."""
        from core.epub_translation.runtime.adapter import translate_epub_translation_input
        from core.epub_translation.runtime.epub_packager import pack_epub_resource_aware, EpubPackagingInput
        from core.epub_translation.reader_chapter_map import build_epub_reader_chapter_map_with_metadata

        # Run EPUB translation
        translation_result = translate_epub_translation_input(options, root=self._root_path)

        # Dry-run: canonical runtime already skipped provider calls. Do NOT package
        # a (bogus) EPUB; report an explicit dry_run terminal state instead.
        if getattr(options, "dry_run", False):
            return {
                "status": "dry_run",
                "input": str(options.translation_input.source_epub_path),
                "output": "",
                "output_dir": str(
                    epub_output_dir(
                        options.translation_input.source_epub_path.parent,
                        options.translation_input.metadata.identifier,
                    )
                ),
                "chunk_total": translation_result.total_chunks,
                "chunk_successful": translation_result.success_count,
                "chunk_failed": translation_result.failed_count,
                "error": "",
                "summary": {
                    "total_chunks": translation_result.total_chunks,
                    "successful_chunks": translation_result.success_count,
                    "failed_chunks": translation_result.failed_count,
                    "chapter_count": translation_result.total_chapters,
                },
                "pipeline_mode": "epub",
                "session_id": translation_result.session_id,
            }

        # If translation successful, package into EPUB
        if translation_result.aggregate_status in ("success", "incomplete"):
            # Build reader chapter map
            reader_result = build_epub_reader_chapter_map_with_metadata(
                translation_result=translation_result,
                translation_input=options.translation_input,
            )

            # Package EPUB
            output_dir = epub_output_dir(
                options.translation_input.source_epub_path.parent,
                options.translation_input.metadata.identifier,
            )
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{options.translation_input.source_epub_path.stem}_zh.epub"

            packaging_input = EpubPackagingInput(
                reader_chapter_map_result=reader_result,
                translation_input=options.translation_input,
                translation_result=translation_result,
            )

            packaging_result = pack_epub_resource_aware(
                packaging_input=packaging_input,
                output_path=output_path,
            )

            # Return result compatible with UI expectations
            return {
                "status": "success" if packaging_result.success else "incomplete",
                "input": str(options.translation_input.source_epub_path),
                "output": str(packaging_result.output_path) if packaging_result.output_path else "",
                "output_dir": str(output_dir),
                "chunk_total": translation_result.total_chunks,
                "chunk_successful": translation_result.success_count,
                "chunk_failed": translation_result.failed_count,
                "error": packaging_result.error_message,
                "summary": {
                    "total_chunks": translation_result.total_chunks,
                    "successful_chunks": translation_result.success_count,
                    "failed_chunks": translation_result.failed_count,
                    "chapter_count": translation_result.total_chapters,
                },
                "pipeline_mode": "epub",
                "session_id": translation_result.session_id,
            }
        else:
            # Translation failed
            return {
                "status": "failed",
                "input": str(options.translation_input.source_epub_path),
                "output": "",
                "output_dir": str(options.translation_input.source_epub_path.parent),
                "chunk_total": translation_result.total_chunks,
                "chunk_successful": translation_result.success_count,
                "chunk_failed": translation_result.failed_count,
                "error": "EPUB translation failed",
                "summary": {
                    "total_chunks": translation_result.total_chunks,
                    "successful_chunks": translation_result.success_count,
                    "failed_chunks": translation_result.failed_count,
                    "chapter_count": translation_result.total_chapters,
                },
                "pipeline_mode": "epub",
                "session_id": translation_result.session_id,
            }

    def _poll_progress(self) -> None:
        """Poll live progress JSON file."""
        while self._poll_running:
            if self._live_progress_path and self._live_progress_path.exists():
                try:
                    content = self._live_progress_path.read_text(encoding="utf-8")
                    progress = json.loads(content)
                    if self._progress_callback:
                        self._progress_callback(progress)
                except Exception:
                    pass
            time.sleep(1.0)

    def _emit_final_progress(self, result: dict) -> None:
        """Emit final progress based on result."""
        status = result.get("status", "unknown")
        chunk_total = result.get("chunk_total", 0)
        chunk_successful = result.get("chunk_successful", 0)
        chunk_failed = result.get("chunk_failed", 0)

        if status == "success":
            progress = {
                "status": "completed",
                "chunk_total": chunk_total,
                "chunk_completed": chunk_successful,
                "message": f"翻譯完成：{chunk_successful}/{chunk_total}",
            }
        elif status == "incomplete":
            progress = {
                "status": "incomplete",
                "chunk_total": chunk_total,
                "chunk_completed": chunk_successful,
                "chunk_failed": chunk_failed,
                "message": f"翻譯未完成：{chunk_successful}/{chunk_total} 成功，{chunk_failed} 失敗",
            }
        elif status == "dry_run":
            progress = {
                "status": "dry_run",
                "chunk_total": chunk_total,
                "chunk_completed": chunk_total,
                "message": "Dry-Run 已完成",
            }
        else:
            progress = {
                "status": "failed",
                "chunk_total": chunk_total,
                "chunk_completed": chunk_successful,
                "error": result.get("error", "Unknown error"),
                "message": f"翻譯失敗：{result.get('error', 'Unknown error')}",
            }
        if self._progress_callback:
            self._progress_callback(progress)

    def cancel(self) -> None:
        """Cancel the translation."""
        self._cancelled = True
        self._poll_running = False

    def is_finished(self) -> bool:
        """Check if worker has finished."""
        return self._finished

    def is_cancelled(self) -> bool:
        """Check if worker was cancelled."""
        return self._cancelled

    def get_result(self) -> Optional[dict]:
        """Get translation result."""
        return self._result

    def get_error(self) -> Optional[str]:
        """Get translation error."""
        return self._error


class TranslationRunner:
    """Manages translation worker thread lifecycle (Tkinter version)."""

    def __init__(self, options: Any, root_path: Path) -> None:
        self._worker = TranslationWorker(options, root_path)
        self._thread: Optional[threading.Thread] = None
        self._completed = False
        self._completion_lock = threading.Lock()

    def start(
        self,
        on_progress: Callable[[dict], None],
        on_finished: Callable[[dict], None],
        on_error: Callable[[str], None],
    ) -> None:
        # Wrap callbacks to track completion
        def wrapped_on_progress(progress: dict) -> None:
            on_progress(progress)

        def wrapped_on_finished(result: dict) -> None:
            on_finished(result)
            with self._completion_lock:
                self._completed = True

        def wrapped_on_error(error: str) -> None:
            on_error(error)
            with self._completion_lock:
                self._completed = True

        self._worker.set_callbacks(wrapped_on_progress, wrapped_on_finished, wrapped_on_error)
        self._thread = threading.Thread(target=self._worker.run, daemon=True)
        self._thread.start()

    def cancel(self, timeout: float = 5.0) -> bool:
        """Cancel the translation and wait for thread to finish.

        Returns:
            True if thread finished within timeout, False otherwise.
        """
        self._worker.cancel()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            return not self._thread.is_alive()
        return True

    def is_completed(self) -> bool:
        """Check if translation completed."""
        with self._completion_lock:
            return self._completed

    def is_running(self) -> bool:
        """Check if thread is still running."""
        return self._thread is not None and self._thread.is_alive()