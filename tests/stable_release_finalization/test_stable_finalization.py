from pathlib import Path

from stable_release.finalization import (
    FINALIZATION_OUTPUTS,
    FROZEN_COMPONENTS,
    REQUIRED_PREPARATION_ARTIFACTS,
    REQUIRED_RC_ARTIFACTS,
    StableFinalizationManifest,
    StableFinalizationValidator,
    build_stable_finalization_artifacts,
    create_stable_finalization_manifest,
    load_stable_finalization_manifest,
)


def seed_required_artifacts(root: Path) -> None:
    for name in REQUIRED_RC_ARTIFACTS:
        (root / name).write_text("PASS\n", encoding="utf-8")
    for name in REQUIRED_PREPARATION_ARTIFACTS:
        if name == "Stable_Release_Preparation_Manifest_1_0_0.json":
            (root / name).write_text(
                '{"stage":"STABLE.1","version":"1.0.0","passed":true}\n',
                encoding="utf-8",
            )
        else:
            (root / name).write_text("PASS\n", encoding="utf-8")


def test_stable_finalization_manifest_valid():
    manifest = create_stable_finalization_manifest(source_stage="STABLE.1")
    assert manifest.validate()
    assert manifest.version == "1.0.0"
    assert manifest.status == "FINALIZED"
    assert manifest.release_channel == "stable"
    assert len(manifest.finalization_hash()) == 64
    assert "stable_preparation" in FROZEN_COMPONENTS
    assert "RELEASE_NOTES_NTPE_1_0_0.md" in FINALIZATION_OUTPUTS


def test_stable_finalization_validator_passes(tmp_path):
    seed_required_artifacts(tmp_path)
    result = StableFinalizationValidator(tmp_path, StableFinalizationManifest()).run()
    assert result["status"] == "PASS"
    assert result["passed"] is True
    assert result["validation"]["component_validation"] is True
    assert result["validation"]["required_preparation_artifacts_valid"] is True
    assert result["validation"]["required_rc_artifacts_valid"] is True
    assert result["validation"]["preparation_manifest_valid"] is True
    assert result["validation"]["public_api_changed"] is False
    assert result["validation"]["product_feature_added"] is False


def test_stable_finalization_reports_written(tmp_path):
    seed_required_artifacts(tmp_path)
    outputs = build_stable_finalization_artifacts(tmp_path)
    expected = {
        "manifest_path",
        "hash_path",
        "Stable_Release_Finalization_Report_1_0_0.md",
        "README_NTPE_1_0_Stable_Final.txt",
        "RELEASE_NOTES_NTPE_1_0_0.md",
        "CHANGELOG_STABLE_FINAL_1_0_0.md",
    }
    assert expected.issubset(set(outputs))
    for path in outputs.values():
        assert Path(path).exists()
    manifest = load_stable_finalization_manifest(outputs["manifest_path"])
    assert manifest["passed"] is True
    assert manifest["stage"] == "STABLE.2"
    assert manifest["status"] == "FINALIZED"
