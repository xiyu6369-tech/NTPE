from pathlib import Path
from translation.consistency_audit import build_translation_consistency_reports

def test_translation_consistency_reports_written(tmp_path):
    reports = build_translation_consistency_reports(tmp_path)
    required = {
        "Translation_Consistency_Audit_Report_RC_04.md",
        "Regression_Report_RC_04.md",
        "Compatibility_Report_RC_04.md",
        "Performance_Report_RC_04.md",
        "Translation_Regression_Report_RC_04.md",
    }
    assert required.issubset(set(reports))
    for path in reports.values():
        assert Path(path).exists()
        assert "PASS" in Path(path).read_text(encoding="utf-8")
