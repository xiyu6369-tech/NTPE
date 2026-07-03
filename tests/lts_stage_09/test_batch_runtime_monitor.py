import json
from pathlib import Path

from core.translation_engine.utils import save_json
from lts.batch_runtime_monitor import BatchMonitorOptions, build_dashboard, format_dashboard_text


def test_batch_runtime_monitor_reads_reports_and_resume(tmp_path: Path):
    output = tmp_path / "output"
    reports = output / "reports"
    output.mkdir()
    reports.mkdir()
    save_json(reports / "Batch_Translation_Report.json", {
        "status": "partial_success",
        "summary": {
            "total_files": 3,
            "completed_files": 3,
            "success": 2,
            "skipped": 0,
            "failed": 1,
            "completion_rate_percent": 100,
            "success_rate_percent": 66.67,
            "elapsed_hms": "00:01:00",
        },
    })
    save_json(reports / "Batch_Failure_Manifest.json", {
        "failed_files": [{"input": "bad.txt", "error": "mock failure"}],
    })
    save_json(output / "book_resume_state.json", {
        "input": "book.txt",
        "chunk_total": 2,
        "updated_at": "2026-07-04T00:00:00",
        "chunks": {
            "1": {"status": "success"},
            "2": {"status": "success"},
        },
    })

    dashboard = build_dashboard(BatchMonitorOptions(output_dir=output), root=tmp_path)

    assert dashboard["version"] == "1.1-lts-stage-09"
    assert dashboard["status"] == "attention_required"
    assert dashboard["summary"]["failed_manifest_count"] == 1
    assert dashboard["summary"]["resume_complete"] == 1
    assert dashboard["summary"]["resume_chunk_progress_percent"] == 100.0
    assert (reports / "Batch_Runtime_Monitor.json").exists()
    assert "failed_manifest_count: 1" in format_dashboard_text(dashboard)


def test_batch_runtime_monitor_handles_missing_report(tmp_path: Path):
    output = tmp_path / "output"
    output.mkdir()
    dashboard = build_dashboard(BatchMonitorOptions(output_dir=output, write_report=False), root=tmp_path)
    assert dashboard["status"] == "no_report"
    assert dashboard["summary"]["batch_status"] == "missing"
