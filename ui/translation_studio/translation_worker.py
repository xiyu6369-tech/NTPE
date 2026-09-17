from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QObject, QThread, Signal, QTimer


class TranslationWorker(QObject):
    """Worker for running canonical TXT translation in background thread."""

    progress_updated = Signal(dict)
    translation_finished = Signal(dict)
    translation_error = Signal(str)

    def __init__(self, options: Any, root_path: Path):
        super().__init__()
        self._options = options
        self._root_path = root_path
        self._runtime = None
        self._live_progress_path: Path | None = None
        self._poll_timer = QTimer()
        self._poll_timer.setInterval(1000)
        self._poll_timer.timeout.connect(self._poll_progress)
        self._cancelled = False
        self._finished = False

    def run(self) -> None:
        """Execute translation in background thread."""
        try:
            from core.translation_runtime import TranslationRuntime

            self._runtime = TranslationRuntime(root=self._root_path)

            self._live_progress_path = (
                self._options.output_dir
                / f"{self._options.input_path.stem}_live_progress.json"
            )

            self.progress_updated.emit({"status": "preparing", "message": "準備翻譯..."})

            self._poll_timer.start()

            result = self._runtime.translate_txt(self._options)

            self._poll_timer.stop()
            self._emit_final_progress(result)

            if not self._cancelled:
                self.translation_finished.emit(result)

        except Exception as e:
            self._poll_timer.stop()
            if not self._cancelled:
                self.translation_error.emit(str(e))
        finally:
            self._finished = True

    def _poll_progress(self) -> None:
        """Poll live progress JSON file."""
        if not self._live_progress_path or not self._live_progress_path.exists():
            return

        try:
            content = self._live_progress_path.read_text(encoding="utf-8")
            progress = json.loads(content)
            self.progress_updated.emit(progress)
        except Exception:
            pass

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
        else:
            progress = {
                "status": "failed",
                "chunk_total": chunk_total,
                "chunk_completed": chunk_successful,
                "error": result.get("error", "Unknown error"),
                "message": f"翻譯失敗：{result.get('error', 'Unknown error')}",
            }
        self.progress_updated.emit(progress)

    def cancel(self) -> None:
        """Cancel the translation."""
        self._cancelled = True
        self._poll_timer.stop()

    def is_finished(self) -> bool:
        """Check if worker has finished."""
        return self._finished

    def is_cancelled(self) -> bool:
        """Check if worker was cancelled."""
        return self._cancelled


class TranslationRunner:
    """Manages translation worker thread lifecycle."""

    def __init__(self, options: Any, root_path: Path):
        self._thread = QThread()
        self._worker = TranslationWorker(options, root_path)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        # Connect thread finished signal for cleanup
        self._thread.finished.connect(self._on_thread_finished)
        self._completed = False

    def start(
        self,
        on_progress: Callable[[dict], None],
        on_finished: Callable[[dict], None],
        on_error: Callable[[str], None],
    ) -> None:
        self._worker.progress_updated.connect(on_progress)
        self._worker.translation_finished.connect(on_finished)
        self._worker.translation_error.connect(on_error)
        # Also disconnect when done to prevent leaks
        self._worker.translation_finished.connect(self._on_worker_finished)
        self._worker.translation_error.connect(self._on_worker_finished)
        self._thread.start()

    def _on_worker_finished(self) -> None:
        """Called when worker finishes (success or error)."""
        self._completed = True
        # Disconnect all signals to prevent leaks
        try:
            self._worker.progress_updated.disconnect()
        except TypeError:
            pass
        try:
            self._worker.translation_finished.disconnect()
        except TypeError:
            pass
        try:
            self._worker.translation_error.disconnect()
        except TypeError:
            pass
        # Quit the thread
        self._thread.quit()

    def _on_thread_finished(self) -> None:
        """Called when thread finishes."""
        pass

    def cancel(self, timeout: int = 5000) -> bool:
        """Cancel the translation and wait for thread to finish.

        Returns:
            True if thread finished within timeout, False otherwise.
        """
        self._worker.cancel()
        if self._thread.isRunning():
            self._thread.quit()
            return self._thread.wait(timeout)
        return True

    def is_completed(self) -> bool:
        """Check if translation completed."""
        return self._completed

    def is_running(self) -> bool:
        """Check if thread is still running."""
        return self._thread.isRunning()