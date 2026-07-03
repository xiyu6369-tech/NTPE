from release_candidate.rc_freeze import (
    FROZEN_COMPONENTS,
    REQUIRED_REPORTS,
    RCFreezeManifest,
    RCFreezeValidator,
    create_rc_freeze_manifest,
)


def test_rc_freeze_manifest_valid():
    manifest = create_rc_freeze_manifest(source="rc5")
    assert manifest.validate()
    assert manifest.status == "FROZEN"
    assert len(manifest.freeze_hash()) == 64


def test_rc_freeze_validator_passes():
    result = RCFreezeValidator(RCFreezeManifest()).run()
    assert result["status"] == "PASS"
    assert result["component_validation"] is True
    assert result["report_validation"] is True
    assert result["manifest_validation"] is True


def test_rc_freeze_required_coverage():
    assert "runtime_api" in FROZEN_COMPONENTS
    assert "external_api" in FROZEN_COMPONENTS
    assert "web_ui" in FROZEN_COMPONENTS
    assert "Release_Candidate_Validation_Report_RC_05.md" in REQUIRED_REPORTS
