from pathlib import Path
from release_candidate.validation import build_rc_validation_reports


def test_release_candidate_reports_written(tmp_path):
    for name in [
        "Regression_Report_RC_04.md",
        "Compatibility_Report_RC_04.md",
        "Performance_Report_RC_04.md",
        "Translation_Consistency_Audit_Report_RC_04.md",
        "Translation_Regression_Report_RC_04.md",
    ]:
        (tmp_path / name).write_text("Result: PASS", encoding="utf-8")
    reports = build_rc_validation_reports(tmp_path)
    required = {
        "Release_Candidate_Validation_Report_RC_05.md",
        "Regression_Report_RC_05.md",
        "Compatibility_Report_RC_05.md",
        "Performance_Report_RC_05.md",
        "Translation_Regression_Report_RC_05.md",
    }
    assert required.issubset(set(reports))
    for path in reports.values():
        assert Path(path).exists()
        assert "PASS" in Path(path).read_text(encoding="utf-8")
