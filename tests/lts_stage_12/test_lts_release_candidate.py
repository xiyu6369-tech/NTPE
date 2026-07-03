from __future__ import annotations

import json
from pathlib import Path

from lts.release_candidate import (
    LTS_RELEASE_CANDIDATE_VERSION,
    LTSReleaseCandidateOptions,
    build_lts_release_candidate_manifest,
    format_lts_release_candidate_release_notes,
    format_lts_release_candidate_text,
    validate_lts_release_candidate,
)


def test_lts_release_candidate_manifest_ready_for_current_project():
    manifest = build_lts_release_candidate_manifest(LTSReleaseCandidateOptions(root=Path.cwd(), write_files=False))
    result = validate_lts_release_candidate(manifest)
    assert manifest["version"] == LTS_RELEASE_CANDIDATE_VERSION
    assert manifest["status"] == "ready"
    assert result["status"] == "pass"
    assert result["missing_count"] == 0
    assert manifest["candidate"]["recommended_tag"] == "v1.1.0-lts-rc-01"


def test_lts_release_candidate_writes_manifest_hash_report_and_notes(tmp_path: Path):
    manifest = build_lts_release_candidate_manifest(
        LTSReleaseCandidateOptions(root=Path.cwd(), rc_dir=tmp_path / "rc")
    )
    manifest_path = Path(manifest["manifest_path"])
    hash_path = Path(manifest["hash_path"])
    report_path = Path(manifest["report_path"])
    notes_path = Path(manifest["release_notes_path"])
    assert manifest_path.exists()
    assert hash_path.exists()
    assert report_path.exists()
    assert notes_path.exists()
    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    saved_hash = json.loads(hash_path.read_text(encoding="utf-8"))
    assert saved["status"] == "ready"
    assert saved_hash["status"] == "ready"
    assert "Release Candidate Preparation" in report_path.read_text(encoding="utf-8")
    assert "NTPE 1.1 LTS Release Candidate Notes" in notes_path.read_text(encoding="utf-8")


def test_lts_release_candidate_text_and_notes_contain_release_gate():
    manifest = build_lts_release_candidate_manifest(LTSReleaseCandidateOptions(root=Path.cwd(), write_files=False))
    text = format_lts_release_candidate_text(manifest)
    notes = format_lts_release_candidate_release_notes(manifest)
    assert "validation: pass" in text
    assert "recommended_tag: v1.1.0-lts-rc-01" in text
    assert "Release Gate" in notes


def test_lts_release_candidate_detects_missing_inputs(tmp_path: Path):
    manifest = build_lts_release_candidate_manifest(LTSReleaseCandidateOptions(root=tmp_path, write_files=False))
    result = validate_lts_release_candidate(manifest)
    assert manifest["status"] == "incomplete"
    assert result["status"] == "fail"
    assert result["missing_count"] > 0
