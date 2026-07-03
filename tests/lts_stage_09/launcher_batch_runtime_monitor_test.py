import subprocess
import sys
from pathlib import Path

from core.translation_engine.utils import save_json


def test_ntpe_batch_monitor_launcher(tmp_path: Path):
    output = tmp_path / "output"
    reports = output / "reports"
    reports.mkdir(parents=True)
    save_json(reports / "Batch_Translation_Report.json", {
        "status": "success",
        "summary": {
            "total_files": 1,
            "completed_files": 1,
            "success": 1,
            "skipped": 0,
            "failed": 0,
            "completion_rate_percent": 100,
            "success_rate_percent": 100,
            "elapsed_hms": "00:00:01",
        },
    })
    save_json(reports / "Batch_Failure_Manifest.json", {"failed_files": []})
    result = subprocess.run(
        [sys.executable, "ntpe_batch_monitor.py", str(output), "--no-write-report"],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "NTPE 1.1 LTS Batch Runtime Monitor" in result.stdout
    assert "status: success" in result.stdout
