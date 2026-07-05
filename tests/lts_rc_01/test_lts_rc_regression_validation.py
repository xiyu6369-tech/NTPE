from __future__ import annotations

import json
from pathlib import Path

from lts.regression_validation import (
    LTS_RC_REGRESSION_VERSION,
    LTSRCRegressionOptions,
    build_lts_rc_regression_manifest,
    format_lts_rc_regression_text,
    validate_lts_rc_regression,
)


def test_lts_rc_regression_manifest_passes_for_current_project():
    manifest = build_lts_rc_regression_manifest(LTSRCRegressionOptions(root=Path.cwd(), write_files=False))
    result = validate_lts_rc_regression(manifest)
    assert manifest["version"] == LTS_RC_REGRESSION_VERSION
    assert manifest["stage"] == "RC-01 Regression Validation"
    assert result["status"] == "pass"
    assert result["failure_count"] == 0
    assert manifest["candidate"]["recommended_tag"] == "v1.1.0-lts-rc-01-regression"


def test_lts_rc_regression_writes_manifest_hash_and_report(tmp_path: Path):
    manifest = build_lts_rc_regression_manifest(
        LTSRCRegressionOptions(root=Path.cwd(), regression_dir=tmp_path / "regression")
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
    assert "Regression Validation" in report_path.read_text(encoding="utf-8")


def test_lts_rc_regression_text_contains_gate_summary():
    manifest = build_lts_rc_regression_manifest(LTSRCRegressionOptions(root=Path.cwd(), write_files=False))
    text = format_lts_rc_regression_text(manifest)
    assert "validation: pass" in text
    assert "failure_count: 0" in text
    assert "recommended_tag: v1.1.0-lts-rc-01-regression" in text


def test_lts_rc_regression_detects_missing_project_inputs(tmp_path: Path):
    manifest = build_lts_rc_regression_manifest(LTSRCRegressionOptions(root=tmp_path, write_files=False))
    result = validate_lts_rc_regression(manifest)
    assert manifest["status"] == "fail"
    assert result["status"] == "fail"
    assert result["failure_count"] > 0
