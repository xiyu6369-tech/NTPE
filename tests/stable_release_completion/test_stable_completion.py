from pathlib import Path

from stable_release.completion import (
    COMPLETION_OUTPUTS,
    FROZEN_COMPONENTS,
    REQUIRED_FINALIZATION_ARTIFACTS,
    REQUIRED_PREPARATION_ARTIFACTS,
    REQUIRED_RC_ARTIFACTS,
    StableCompletionManifest,
    StableCompletionValidator,
    build_stable_completion_artifacts,
    create_stable_completion_manifest,
    load_stable_completion_manifest,
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
    for name in REQUIRED_FINALIZATION_ARTIFACTS:
        if name == "Stable_Release_Finalization_Manifest_1_0_0.json":
            (root / name).write_text(
                '{"stage":"STABLE.2","version":"1.0.0","status":"FINALIZED","passed":true}\n',
                encoding="utf-8",
            )
        else:
            (root / name).write_text("PASS\n", encoding="utf-8")


def test_stable_completion_manifest_valid():
    manifest = create_stable_completion_manifest(source_stage="STABLE.2")
    assert manifest.validate()
    assert manifest.version == "1.0.0"
    assert manifest.status == "COMPLETE"
    assert manifest.release_channel == "stable"
    assert len(manifest.completion_hash()) == 64
    assert "stable_finalization" in FROZEN_COMPONENTS
    assert "Stable_Release_Complete_Report_1_0_0.md" in COMPLETION_OUTPUTS


def test_stable_completion_validator_passes(tmp_path):
    seed_required_artifacts(tmp_path)
    result = StableCompletionValidator(tmp_path, StableCompletionManifest()).run()
    assert result["status"] == "PASS"
    assert result["passed"] is True
    assert result["validation"]["component_validation"] is True
    assert result["validation"]["required_finalization_artifacts_valid"] is True
    assert result["validation"]["required_preparation_artifacts_valid"] is True
    assert result["validation"]["required_rc_artifacts_valid"] is True
    assert result["validation"]["finalization_manifest_valid"] is True
    assert result["validation"]["public_api_changed"] is False
    assert result["validation"]["product_feature_added"] is False


def test_stable_completion_reports_written(tmp_path):
    seed_required_artifacts(tmp_path)
    outputs = build_stable_completion_artifacts(tmp_path)
    expected = {
        "manifest_path",
        "hash_path",
        "Stable_Release_Complete_Report_1_0_0.md",
        "README_NTPE_1_0_Stable_Release_Complete.txt",
        "CHANGELOG_STABLE_COMPLETE_1_0_0.md",
    }
    assert expected.issubset(set(outputs))
    for path in outputs.values():
        assert Path(path).exists()
    manifest = load_stable_completion_manifest(outputs["manifest_path"])
    assert manifest["passed"] is True
    assert manifest["stage"] == "STABLE.3"
    assert manifest["status"] == "COMPLETE"
