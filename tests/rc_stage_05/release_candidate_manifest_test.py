from pathlib import Path
from release_candidate.validation import build_rc_validation_manifest, load_rc_validation_manifest


def test_release_candidate_manifest_written(tmp_path):
    # Seed required RC.4 report names so the validation is self-contained in tmp_path.
    for name in [
        "Regression_Report_RC_04.md",
        "Compatibility_Report_RC_04.md",
        "Performance_Report_RC_04.md",
        "Translation_Consistency_Audit_Report_RC_04.md",
        "Translation_Regression_Report_RC_04.md",
    ]:
        (tmp_path / name).write_text("Result: PASS", encoding="utf-8")
    output = build_rc_validation_manifest(tmp_path)
    manifest_path = Path(output["manifest_path"])
    hash_path = Path(output["hash_path"])
    assert manifest_path.exists()
    assert hash_path.exists()
    manifest = load_rc_validation_manifest(manifest_path)
    assert manifest["passed"] is True
    assert manifest["stage"] == "RC.5"
