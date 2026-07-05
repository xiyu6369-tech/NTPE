from pathlib import Path

from lts.stable_complete import (
    LTSStableCompleteOptions,
    build_completion_marker_markdown,
    build_lts_stable_complete_manifest,
    format_lts_stable_complete_text,
    validate_lts_stable_complete,
)


def test_lts_stable_complete_manifest_passes_for_current_project():
    manifest = build_lts_stable_complete_manifest(
        LTSStableCompleteOptions(write_files=False)
    )
    result = validate_lts_stable_complete(manifest)
    assert result["status"] == "pass"
    assert result["failure_count"] == 0
    assert manifest["stable_complete_ready"] is True
    assert manifest["completion_scope"]["release_state"] == "complete"
    assert manifest["candidate"]["recommended_tag"] == "v1.1.0-lts-stable"


def test_lts_stable_complete_writes_manifest_hash_report_and_marker(tmp_path: Path):
    manifest = build_lts_stable_complete_manifest(
        LTSStableCompleteOptions(stable_dir=tmp_path / "stable_complete", write_files=True)
    )
    manifest_path = Path(manifest["manifest_path"])
    hash_path = Path(manifest["hash_path"])
    report_path = Path(manifest["report_path"])
    marker_path = Path(manifest["completion_marker_path"])
    assert manifest_path.exists()
    assert hash_path.exists()
    assert report_path.exists()
    assert marker_path.exists()
    assert "Stable Release Complete Report" in report_path.read_text(encoding="utf-8")
    assert "NTPE 1.1 LTS Stable Release Complete" in marker_path.read_text(encoding="utf-8")


def test_lts_stable_complete_text_contains_summary():
    manifest = build_lts_stable_complete_manifest(
        LTSStableCompleteOptions(write_files=False)
    )
    text = format_lts_stable_complete_text(manifest)
    assert "NTPE 1.1 LTS Stable Release Complete" in text
    assert "stable_complete_ready: True" in text
    assert "v1.1.0-lts-stable" in text


def test_lts_stable_complete_detects_missing_project_inputs(tmp_path: Path):
    manifest = build_lts_stable_complete_manifest(
        LTSStableCompleteOptions(root=tmp_path, write_files=False)
    )
    result = validate_lts_stable_complete(manifest)
    assert result["status"] == "fail"
    assert result["failure_count"] > 0


def test_completion_marker_describes_lts_capabilities():
    manifest = build_lts_stable_complete_manifest(
        LTSStableCompleteOptions(write_files=False)
    )
    marker = build_completion_marker_markdown(manifest)
    assert "Batch folder translation" in marker
    assert "Taiwan Traditional Chinese normalization" in marker
    assert "No external API calls" in marker
