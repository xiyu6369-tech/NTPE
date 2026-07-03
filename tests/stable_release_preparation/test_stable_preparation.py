from pathlib import Path

from stable_release.preparation import (
    FROZEN_COMPONENTS,
    REQUIRED_RC_ARTIFACTS,
    STABLE_OUTPUTS,
    StablePreparationManifest,
    StablePreparationValidator,
    build_stable_preparation_artifacts,
    create_stable_preparation_manifest,
    load_stable_preparation_manifest,
)


def seed_required_rc_artifacts(root: Path) -> None:
    for name in REQUIRED_RC_ARTIFACTS:
        (root / name).write_text("PASS\n", encoding="utf-8")


def test_stable_preparation_manifest_valid():
    manifest = create_stable_preparation_manifest(source_stage="RC.6")
    assert manifest.validate()
    assert manifest.version == "1.0.0"
    assert manifest.source_version == "1.0-rc"
    assert len(manifest.preparation_hash()) == 64
    assert "release_candidate" in FROZEN_COMPONENTS
    assert "Stable_Release_Preparation_Report_1_0_0.md" in STABLE_OUTPUTS


def test_stable_preparation_validator_passes(tmp_path):
    seed_required_rc_artifacts(tmp_path)
    result = StablePreparationValidator(tmp_path, StablePreparationManifest()).run()
    assert result["status"] == "PASS"
    assert result["passed"] is True
    assert result["validation"]["component_validation"] is True
    assert result["validation"]["required_rc_artifacts_valid"] is True
    assert result["validation"]["public_api_changed"] is False
    assert result["validation"]["product_feature_added"] is False


def test_stable_preparation_reports_written(tmp_path):
    seed_required_rc_artifacts(tmp_path)
    outputs = build_stable_preparation_artifacts(tmp_path)
    expected = {
        "manifest_path",
        "hash_path",
        "Stable_Release_Preparation_Report_1_0_0.md",
        "README_NTPE_1_0_Stable_Release_Preparation.txt",
        "CHANGELOG_STABLE_1_0_0.md",
    }
    assert expected.issubset(set(outputs))
    for path in outputs.values():
        assert Path(path).exists()
    manifest = load_stable_preparation_manifest(outputs["manifest_path"])
    assert manifest["passed"] is True
    assert manifest["stage"] == "STABLE.1"
