from __future__ import annotations

from pathlib import Path

from core.translation_runtime import TranslationRuntime
from core.translation_runtime.runtime_recovery import RuntimeCheckpointKey, load_checkpoint, recovery_summary, update_checkpoint


def test_runtime_checkpoint_lifecycle(tmp_path: Path) -> None:
    key = RuntimeCheckpointKey(scope="txt", name="sample.txt")
    checkpoint = update_checkpoint(tmp_path, key, cursor={"chunk_index": 2, "chunk_total": 5})

    assert checkpoint.status == "running"
    assert checkpoint.cursor["chunk_index"] == 2

    loaded = load_checkpoint(tmp_path, key)
    assert loaded.cursor["chunk_total"] == 5

    update_checkpoint(tmp_path, key, status="failed", error={"code": "TIMEOUT", "message": "provider timeout"})
    failed = load_checkpoint(tmp_path, key)
    assert failed.status == "failed"
    assert failed.errors[-1]["code"] == "TIMEOUT"


def test_runtime_facade_exposes_recovery_contract(tmp_path: Path) -> None:
    runtime = TranslationRuntime(root=tmp_path)
    compatibility = runtime.validate_compatibility()
    assert compatibility["status"] == "success"
    assert "checkpoint" not in compatibility["missing_entrypoints"]

    running = runtime.checkpoint("batch", "novel-folder", file_index=3, total_files=10)
    assert running["status"] == "running"
    assert running["cursor"]["file_index"] == 3

    completed = runtime.checkpoint_completed("batch", "novel-folder", output="done")
    assert completed["status"] == "success"

    summary = runtime.recovery_summary()
    assert summary["status"] == "success"
    assert summary["total"] == 1
    assert summary["status_counts"]["success"] == 1


def test_recovery_summary_handles_empty_project(tmp_path: Path) -> None:
    summary = recovery_summary(tmp_path)
    assert summary["status"] == "success"
    assert summary["total"] == 0
    assert summary["status_counts"] == {}
