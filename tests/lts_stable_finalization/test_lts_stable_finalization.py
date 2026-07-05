from pathlib import Path

from lts.stable_finalization import (
    LTSStableFinalizationOptions,
    build_lts_stable_finalization_manifest,
    build_release_notes_markdown,
    format_lts_stable_finalization_text,
    validate_lts_stable_finalization,
)


def test_lts_stable_finalization_manifest_passes_for_current_project():
    manifest = build_lts_stable_finalization_manifest(
        LTSStableFinalizationOptions(write_files=False)
    )
    result = validate_lts_stable_finalization(manifest)
    assert result["status"] == "pass"
    assert result["failure_count"] == 0
    assert manifest["stable_finalization_ready"] is True
    assert manifest["stable_final_scope"]["feature_changes_allowed"] is False


def test_lts_stable_finalization_writes_manifest_hash_report_and_notes(tmp_path: Path):
    manifest = build_lts_stable_finalization_manifest(
        LTSStableFinalizationOptions(stable_dir=tmp_path / "stable_final", write_files=True)
    )
    manifest_path = Path(manifest["manifest_path"])
    hash_path = Path(manifest["hash_path"])
    report_path = Path(manifest["report_path"])
    release_notes_path = Path(manifest["release_notes_path"])
    assert manifest_path.exists()
    assert hash_path.exists()
    assert report_path.exists()
    assert release_notes_path.exists()
    assert "Stable Release Finalization Report" in report_path.read_text(encoding="utf-8")
    assert "NTPE 1.1 LTS Release Notes" in release_notes_path.read_text(encoding="utf-8")


def test_lts_stable_finalization_text_contains_summary():
    manifest = build_lts_stable_finalization_manifest(
        LTSStableFinalizationOptions(write_files=False)
    )
    text = format_lts_stable_finalization_text(manifest)
    assert "NTPE 1.1 LTS Stable Release Finalization" in text
    assert "stable_finalization_ready: True" in text
    assert "v1.1.0-lts-stable-finalization" in text


def test_lts_stable_finalization_detects_missing_project_inputs(tmp_path: Path):
    manifest = build_lts_stable_finalization_manifest(
        LTSStableFinalizationOptions(root=tmp_path, write_files=False)
    )
    result = validate_lts_stable_finalization(manifest)
    assert result["status"] == "fail"
    assert result["failure_count"] > 0


def test_release_notes_describe_clean_packaging_policy():
    manifest = build_lts_stable_finalization_manifest(
        LTSStableFinalizationOptions(write_files=False)
    )
    notes = build_release_notes_markdown(manifest)
    assert "Clean Project Tool" in notes
    assert "Batch folder translation" in notes
    assert "No external API calls" in notes
