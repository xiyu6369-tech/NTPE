from __future__ import annotations

import json
from pathlib import Path

from lts.final_validation import (
    LTS_RC_FINAL_VERSION,
    LTSRCFinalValidationOptions,
    build_lts_rc_final_validation_manifest,
    format_lts_rc_final_validation_text,
    validate_lts_rc_final_validation,
)


def test_lts_rc_final_validation_manifest_passes_for_current_project():
    manifest = build_lts_rc_final_validation_manifest(
        LTSRCFinalValidationOptions(root=Path.cwd(), write_files=False)
    )
    result = validate_lts_rc_final_validation(manifest)
    assert manifest["version"] == LTS_RC_FINAL_VERSION
    assert manifest["stage"] == "RC-05 Release Candidate Final Validation"
    assert result["status"] == "pass"
    assert result["failure_count"] == 0
    assert manifest["candidate"]["recommended_tag"] == "v1.1.0-lts-rc-05-final-validation"
    assert manifest["release_candidate_gate_ready"] is True


def test_lts_rc_final_validation_writes_manifest_hash_and_report(tmp_path: Path):
    manifest = build_lts_rc_final_validation_manifest(
        LTSRCFinalValidationOptions(root=Path.cwd(), final_dir=tmp_path / "final")
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
    assert "Release Candidate Final Validation" in report_path.read_text(encoding="utf-8")


def test_lts_rc_final_validation_text_contains_gate_summary():
    manifest = build_lts_rc_final_validation_manifest(
        LTSRCFinalValidationOptions(root=Path.cwd(), write_files=False)
    )
    text = format_lts_rc_final_validation_text(manifest)
    assert "validation: pass" in text
    assert "failure_count: 0" in text
    assert "release_candidate_gate_ready: True" in text
    assert "recommended_tag: v1.1.0-lts-rc-05-final-validation" in text


def test_lts_rc_final_validation_detects_missing_project_inputs(tmp_path: Path):
    manifest = build_lts_rc_final_validation_manifest(
        LTSRCFinalValidationOptions(root=tmp_path, write_files=False)
    )
    result = validate_lts_rc_final_validation(manifest)
    assert manifest["status"] == "fail"
    assert result["status"] == "fail"
    assert result["failure_count"] > 0
