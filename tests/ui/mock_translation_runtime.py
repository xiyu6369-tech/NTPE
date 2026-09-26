"""Mock TranslationRuntime for GUI testing without NVIDIA API."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any


class MockTranslationRuntime:
    """Mock runtime that simulates translation with live progress file.
    
    Configurable via class attributes or instance attributes:
    - result_mode: 'success', 'incomplete', 'failed', 'exception'
    - chunk_total: number of chunks to simulate
    - chunk_delay: delay between chunks (seconds)
    - exception_message: message when raising exception
    """

    # Class-level defaults (can be overridden per instance)
    result_mode = "success"
    chunk_total = 5
    chunk_delay = 0.5
    exception_message = "Mock runtime exception"

    def __init__(self, root: Path | str | None = None, api_key: str | None = None):
        self.root = Path(root) if root else Path(".")
        # Instance attributes can override class defaults
        self._result_mode = getattr(self, 'result_mode', 'success')
        self._chunk_total = getattr(self, 'chunk_total', 5)
        self._chunk_delay = getattr(self, 'chunk_delay', 0.5)
        self._exception_message = getattr(self, 'exception_message', 'Mock runtime exception')

    def translate_txt(self, options: Any) -> dict:
        """Simulate translation by writing progress to live_progress.json."""
        output_dir = options.output_dir
        input_stem = options.input_path.stem
        live_progress_path = output_dir / f"{input_stem}_live_progress.json"

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        chunk_total = self._chunk_total

        # Write initial progress
        self._write_progress(live_progress_path, {
            "status": "running",
            "chunk_total": chunk_total,
            "chunk_completed": 0,
            "message": "翻譯中..."
        })

        # Simulate chunk processing
        for i in range(1, chunk_total + 1):
            time.sleep(self._chunk_delay)  # Simulate work
            self._write_progress(live_progress_path, {
                "status": "running",
                "chunk_total": chunk_total,
                "chunk_completed": i,
                "message": f"已完成 {i} / {chunk_total}"
            })

        # Handle exception mode
        if self._result_mode == "exception":
            raise Exception(self._exception_message)

        # Write final output file
        final_output = output_dir / f"{input_stem}_zh.txt"
        final_output.parent.mkdir(parents=True, exist_ok=True)
        final_output.write_text(f"Translated content for {input_stem}\n", encoding="utf-8")

        # Return result based on mode
        if self._result_mode == "incomplete":
            return {
                "status": "incomplete",
                "input": str(options.input_path),
                "output": str(final_output),
                "output_dir": str(output_dir),
                "chunk_total": chunk_total,
                "chunk_successful": chunk_total - 2,  # Some failed
                "chunk_failed": 2,
                "error": "Some chunks failed",
                "summary": {
                    "total_chunks": chunk_total,
                    "successful_chunks": chunk_total - 2,
                    "failed_chunks": 2,
                    "elapsed_seconds": chunk_total * self._chunk_delay,
                },
                "pipeline_mode": "mock",
                "session_id": "mock-session-incomplete",
            }
        elif self._result_mode == "failed":
            return {
                "status": "failed",
                "input": str(options.input_path),
                "output": "",
                "output_dir": str(output_dir),
                "chunk_total": chunk_total,
                "chunk_successful": 0,
                "chunk_failed": chunk_total,
                "error": "Translation failed completely",
                "summary": {
                    "total_chunks": chunk_total,
                    "successful_chunks": 0,
                    "failed_chunks": chunk_total,
                    "elapsed_seconds": chunk_total * self._chunk_delay,
                },
                "pipeline_mode": "mock",
                "session_id": "mock-session-failed",
            }
        else:  # success (default)
            return {
                "status": "success",
                "input": str(options.input_path),
                "output": str(final_output),
                "output_dir": str(output_dir),
                "chunk_total": chunk_total,
                "chunk_successful": chunk_total,
                "chunk_failed": 0,
                "summary": {
                    "total_chunks": chunk_total,
                    "successful_chunks": chunk_total,
                    "failed_chunks": 0,
                    "elapsed_seconds": chunk_total * self._chunk_delay,
                },
                "pipeline_mode": "mock",
                "session_id": "mock-session-123",
            }

    def _write_progress(self, path: Path, progress: dict) -> None:
        import json
        path.write_text(json.dumps(progress, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def set_result_mode(cls, mode: str) -> None:
        """Set the result mode for all future instances."""
        cls.result_mode = mode

    @classmethod
    def set_chunk_total(cls, total: int) -> None:
        """Set the chunk total for all future instances."""
        cls.chunk_total = total

    @classmethod
    def set_chunk_delay(cls, delay: float) -> None:
        """Set the chunk delay for all future instances."""
        cls.chunk_delay = delay

    @classmethod
    def set_exception_message(cls, message: str) -> None:
        """Set the exception message for all future instances."""
        cls.exception_message = message


# Patch the real runtime for testing
def install_mock_runtime():
    """Install mock runtime for testing."""
    import core.translation_runtime.runtime as runtime_module
    runtime_module.TranslationRuntime = MockTranslationRuntime
    # Also patch the module where worker imports from
    import core.translation_runtime as core_runtime
    core_runtime.TranslationRuntime = MockTranslationRuntime