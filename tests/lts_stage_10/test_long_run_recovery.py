from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from lts.batch_translation_runtime import BatchTranslationOptions, translate_batch
from lts.long_run_recovery import (
    LongRunRecoveryOptions,
    build_recovery_plan,
    collect_stale_resume_states,
    heartbeat_path,
    write_heartbeat,
)


def test_write_heartbeat_creates_runtime_status(tmp_path: Path):
    report_dir = tmp_path / "reports"
    payload = write_heartbeat(report_dir, status="running", current_file="001.txt", current_index=1, total_files=2, completed_files=0)
    saved = json.loads(heartbeat_path(report_dir).read_text(encoding="utf-8"))
    assert payload["version"] == "1.1-lts-stage-10"
    assert saved["status"] == "running"
    assert saved["current_file"] == "001.txt"
    assert saved["progress_percent"] == 0.0


def test_collect_stale_resume_states_detects_incomplete_old_resume(tmp_path: Path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    old = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    (output_dir / "novel_resume_state.json").write_text(json.dumps({
        "input": "novel.txt",
        "updated_at": old,
        "chunk_total": 3,
        "chunks": {"000001": {"status": "success"}},
    }), encoding="utf-8")
    stale = collect_stale_resume_states(output_dir, stale_after_seconds=60)
    assert len(stale) == 1
    assert stale[0]["reason"] == "stale_incomplete_resume"
    assert stale[0]["progress_percent"] == 33.33


def test_recovery_plan_uses_failure_manifest(tmp_path: Path):
    output_dir = tmp_path / "output"
    report_dir = output_dir / "reports"
    report_dir.mkdir(parents=True)
    (report_dir / "Batch_Failure_Manifest.json").write_text(json.dumps({
        "failed_files": [{"input": "bad.txt", "error": "503"}],
    }), encoding="utf-8")
    plan = build_recovery_plan(LongRunRecoveryOptions(output_dir=output_dir, stale_after_seconds=60), root=tmp_path)
    assert plan["status"] == "recovery_required"
    assert plan["summary"]["failed_manifest_count"] == 1
    assert any(action["type"] == "retry_failed_manifest" for action in plan["actions"])
    assert (report_dir / "Batch_Recovery_Plan.json").exists()


def test_batch_translation_writes_heartbeat_in_dry_run(tmp_path: Path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    (input_dir / "001.txt").write_text("안녕하세요.\n", encoding="utf-8")
    report = translate_batch(BatchTranslationOptions(input_dir=input_dir, output_dir=output_dir, dry_run=True, progress=False, heartbeat=True), root=Path.cwd())
    heartbeat = json.loads((output_dir / "reports" / "Batch_Heartbeat.json").read_text(encoding="utf-8"))
    assert report["version"] == "1.1-lts-stage-10"
    assert heartbeat["status"] == "success"
    assert heartbeat["completed_files"] == 1


def test_recovery_plan_healthy_when_no_failures(tmp_path: Path):
    output_dir = tmp_path / "output"
    (output_dir / "reports").mkdir(parents=True)
    write_heartbeat(output_dir / "reports", status="success", total_files=1, completed_files=1)
    plan = build_recovery_plan(LongRunRecoveryOptions(output_dir=output_dir, stale_after_seconds=1), root=tmp_path)
    assert plan["status"] == "healthy"
    assert plan["summary"]["action_count"] == 0
