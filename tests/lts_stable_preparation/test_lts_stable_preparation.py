from pathlib import Path

from lts.stable_preparation import (
    LTSStablePreparationOptions,
    build_lts_stable_preparation_manifest,
    format_lts_stable_preparation_text,
    validate_lts_stable_preparation,
)


def test_lts_stable_preparation_manifest_passes_for_current_project():
    manifest = build_lts_stable_preparation_manifest(
        LTSStablePreparationOptions(write_files=False)
    )
    result = validate_lts_stable_preparation(manifest)
    assert result["status"] == "pass"
    assert result["failure_count"] == 0
    assert manifest["stable_preparation_ready"] is True
    assert manifest["stable_scope"]["feature_changes_allowed"] is False


def test_lts_stable_preparation_writes_manifest_hash_and_report(tmp_path: Path):
    manifest = build_lts_stable_preparation_manifest(
        LTSStablePreparationOptions(stable_dir=tmp_path / "stable_prep", write_files=True)
    )
    manifest_path = Path(manifest["manifest_path"])
    hash_path = Path(manifest["hash_path"])
    report_path = Path(manifest["report_path"])
    assert manifest_path.exists()
    assert hash_path.exists()
    assert report_path.exists()
    assert "Stable Release Preparation Report" in report_path.read_text(encoding="utf-8")


def test_lts_stable_preparation_text_contains_summary():
    manifest = build_lts_stable_preparation_manifest(
        LTSStablePreparationOptions(write_files=False)
    )
    text = format_lts_stable_preparation_text(manifest)
    assert "NTPE 1.1 LTS Stable Release Preparation" in text
    assert "stable_preparation_ready: True" in text
    assert "v1.1.0-lts-stable-preparation" in text


def test_lts_stable_preparation_detects_missing_project_inputs(tmp_path: Path):
    manifest = build_lts_stable_preparation_manifest(
        LTSStablePreparationOptions(root=tmp_path, write_files=False)
    )
    result = validate_lts_stable_preparation(manifest)
    assert result["status"] == "fail"
    assert result["failure_count"] > 0
