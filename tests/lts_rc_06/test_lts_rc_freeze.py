from __future__ import annotations

import json
from pathlib import Path

from lts.rc_freeze import (
    LTS_RC_FREEZE_VERSION,
    LTSRCFreezeOptions,
    build_lts_rc_freeze_manifest,
    format_lts_rc_freeze_text,
    validate_lts_rc_freeze,
)


def test_lts_rc_freeze_manifest_passes_for_current_project():
    manifest = build_lts_rc_freeze_manifest(
        LTSRCFreezeOptions(root=Path.cwd(), write_files=False)
    )
    result = validate_lts_rc_freeze(manifest)
    assert manifest["version"] == LTS_RC_FREEZE_VERSION
    assert manifest["stage"] == "RC-06 LTS RC Freeze"
    assert result["status"] == "pass"
    assert result["failure_count"] == 0
    assert manifest["candidate"]["recommended_tag"] == "v1.1.0-lts-rc-06-freeze"
    assert manifest["rc_freeze_ready"] is True


def test_lts_rc_freeze_writes_manifest_hash_and_report(tmp_path: Path):
    manifest = build_lts_rc_freeze_manifest(
        LTSRCFreezeOptions(root=Path.cwd(), freeze_dir=tmp_path / "freeze")
    )
    manifest_path = Path(manifest["manifest_path"])
    hash_path = Path(manifest["hash_path"])
    report_path = Path(manifest["report_path"])
    assert manifest_path.exists()
    assert hash_path.exists()
    assert report_path.exists()
    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    saved_hash = json.loads(hash_path.read_text(encoding="utf-8"))
    assert saved["status"] == "pass"
    assert saved_hash["status"] == "pass"
    assert "LTS RC Freeze" in report_path.read_text(encoding="utf-8")


def test_lts_rc_freeze_text_contains_freeze_summary():
    manifest = build_lts_rc_freeze_manifest(
        LTSRCFreezeOptions(root=Path.cwd(), write_files=False)
    )
    text = format_lts_rc_freeze_text(manifest)
    assert "validation: pass" in text
    assert "failure_count: 0" in text
    assert "rc_freeze_ready: True" in text
    assert "recommended_tag: v1.1.0-lts-rc-06-freeze" in text


def test_lts_rc_freeze_detects_missing_project_inputs(tmp_path: Path):
    manifest = build_lts_rc_freeze_manifest(
        LTSRCFreezeOptions(root=tmp_path, write_files=False)
    )
    result = validate_lts_rc_freeze(manifest)
    assert manifest["status"] == "fail"
    assert result["status"] == "fail"
    assert result["failure_count"] > 0
