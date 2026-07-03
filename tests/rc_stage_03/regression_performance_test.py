from pathlib import Path
from performance.stabilization import build_performance_stabilization_reports

ROOT = Path(__file__).resolve().parents[2]

def test_performance_reports_written():
    reports = build_performance_stabilization_reports(ROOT)
    assert "Performance_Stabilization_Report_RC_03.md" in reports
    assert Path(reports["Regression_Report_RC_03.md"]).exists()
