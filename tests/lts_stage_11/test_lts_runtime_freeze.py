from __future__ import annotations

import json
from pathlib import Path

from lts.runtime_freeze import (
    FROZEN_RUNTIME_FILES,
    REQUIRED_STAGE_REPORTS,
    RuntimeFreezeOptions,
    build_runtime_freeze_manifest,
    format_runtime_freeze_text,
    validate_runtime_freeze,
)


def test_runtime_freeze_manifest_builds_for_current_project():
    manifest = build_runtime_freeze_manifest(RuntimeFreezeOptions(root=Path.cwd(), write_files=False))
    result = validate_runtime_freeze(manifest)
    assert manifest["version"] == "1.1-lts-stage-11"
    assert manifest["status"] == "frozen"
    assert result["status"] == "pass"
    assert result["runtime_file_count"] == len(FROZEN_RUNTIME_FILES)
    assert result["stage_report_count"] == len(REQUIRED_STAGE_REPORTS)


def test_runtime_freeze_writes_manifest_hash_and_report(tmp_path: Path):
    manifest = build_runtime_freeze_manifest(RuntimeFreezeOptions(root=Path.cwd(), freeze_dir=tmp_path / "freeze"))
    manifest_path = Path(manifest["manifest_path"])
    hash_path = Path(manifest["hash_path"])
    report_path = Path(manifest["report_path"])
    assert manifest_path.exists()
    assert hash_path.exists()
    assert report_path.exists()
    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    saved_hash = json.loads(hash_path.read_text(encoding="utf-8"))
    assert saved["status"] == "frozen"
    assert saved_hash["status"] == "frozen"
    assert "Runtime Freeze" in report_path.read_text(encoding="utf-8")


def test_runtime_freeze_text_summary_contains_counts():
    manifest = build_runtime_freeze_manifest(RuntimeFreezeOptions(root=Path.cwd(), write_files=False))
    text = format_runtime_freeze_text(manifest)
    assert "NTPE 1.1 LTS Runtime Freeze" in text
    assert "validation: pass" in text
    assert "missing_count: 0" in text


def test_runtime_freeze_detects_missing_files(tmp_path: Path):
    manifest = build_runtime_freeze_manifest(RuntimeFreezeOptions(root=tmp_path, write_files=False))
    result = validate_runtime_freeze(manifest)
    assert manifest["status"] == "incomplete"
    assert result["status"] == "fail"
    assert result["missing_count"] > 0
