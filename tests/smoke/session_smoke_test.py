from __future__ import annotations

from pathlib import Path

from core.translation_runtime import TranslationRuntime


def test_session_smoke(tmp_path: Path) -> None:
    runtime = TranslationRuntime(root=tmp_path)
    result = runtime.create_session(mode="smoke", input_source="sample.txt")
    assert result["status"] == "success"
    assert runtime.list_sessions()["total"] == 1
