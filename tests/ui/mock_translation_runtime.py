"""Mock TranslationRuntime for GUI testing without NVIDIA API."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any


class MockTranslationRuntime:
    """Mock runtime that simulates translation with live progress file."""

    def __init__(self, root: Path | str | None = None, api_key: str | None = None):
        self.root = Path(root) if root else Path(".")

    def translate_txt(self, options: Any) -> dict:
        """Simulate translation by writing progress to live_progress.json."""
        output_dir = options.output_dir
        input_stem = options.input_path.stem
        live_progress_path = output_dir / f"{input_stem}_live_progress.json"

        # Chunk count
        chunk_total = 5

        # Write initial progress
        self._write_progress(live_progress_path, {
            "status": "running",
            "chunk_total": chunk_total,
            "chunk_completed": 0,
            "message": "翻譯中..."
        })

        # Simulate chunk processing
        for i in range(1, chunk_total + 1):
            time.sleep(0.5)  # Simulate work
            self._write_progress(live_progress_path, {
                "status": "running",
                "chunk_total": chunk_total,
                "chunk_completed": i,
                "message": f"已完成 {i} / {chunk_total}"
            })

        # Write final result
        final_output = output_dir / f"{input_stem}_zh.txt"
        final_output.parent.mkdir(parents=True, exist_ok=True)
        final_output.write_text(f"Translated content for {input_stem}\n", encoding="utf-8")

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
                "elapsed_seconds": chunk_total * 0.5,
            },
            "pipeline_mode": "mock",
            "session_id": "mock-session-123",
        }

    def _write_progress(self, path: Path, progress: dict) -> None:
        import json
        path.write_text(json.dumps(progress, ensure_ascii=False), encoding="utf-8")


# Patch the real runtime for testing
def install_mock_runtime():
    """Install mock runtime for testing."""
    import ui.translation_studio.translation_worker as tw_module
    tw_module.TranslationRuntime = MockTranslationRuntime