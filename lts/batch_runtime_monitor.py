from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.translation_engine.utils import now_iso, save_json, save_text
from lts.batch_translation_runtime import DEFAULT_BATCH_FAILURE_BASENAME, DEFAULT_BATCH_REPORT_BASENAME, format_duration, safe_percent

DEFAULT_MONITOR_BASENAME = "Batch_Runtime_Monitor"


@dataclass(frozen=True)
class BatchMonitorOptions:
    output_dir: Path
    report_dir: Path | None = None
    failure_manifest: Path | None = None
    resume_glob: str = "*_resume_state.json"
    write_report: bool = True
    quiet: bool = False


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"status": "unreadable", "error": str(exc), "path": str(path)}


def resolve_report_dir(output_dir: Path, report_dir: Path | None) -> Path:
    return report_dir if report_dir and report_dir.is_absolute() else (output_dir / "reports" if report_dir is None else output_dir / report_dir)


def resolve_failure_manifest(report_dir: Path, failure_manifest: Path | None) -> Path:
    if failure_manifest:
        return failure_manifest if failure_manifest.is_absolute() else report_dir / failure_manifest
    return report_dir / f"{DEFAULT_BATCH_FAILURE_BASENAME}.json"


def collect_resume_states(output_dir: Path, resume_glob: str = "*_resume_state.json") -> list[dict]:
    states: list[dict] = []
    for path in sorted(output_dir.rglob(resume_glob)):
        data = _read_json(path)
        chunks = data.get("chunks", {}) if isinstance(data, dict) else {}
        total = int(data.get("chunk_total", len(chunks)) or len(chunks) or 0)
        completed = sum(1 for item in chunks.values() if isinstance(item, dict) and item.get("status") in {"success", "skipped"})
        failed = sum(1 for item in chunks.values() if isinstance(item, dict) and item.get("status") in {"failed", "qa_failed"})
        states.append({
            "path": str(path),
            "input": data.get("input", ""),
            "updated_at": data.get("updated_at", ""),
            "chunk_total": total,
            "completed_chunks": completed,
            "failed_chunks": failed,
            "progress_percent": safe_percent(completed, total),
            "status": "complete" if total and completed >= total and failed == 0 else "failed" if failed else "in_progress" if completed else "pending",
        })
    return states


def build_dashboard(options: BatchMonitorOptions, root: str | Path | None = None) -> dict:
    root_path = Path(root) if root else Path(__file__).resolve().parents[1]
    output_dir = options.output_dir if options.output_dir.is_absolute() else root_path / options.output_dir
    report_dir = resolve_report_dir(output_dir, options.report_dir)
    batch_report_path = report_dir / f"{DEFAULT_BATCH_REPORT_BASENAME}.json"
    failure_manifest_path = resolve_failure_manifest(report_dir, options.failure_manifest)

    batch_report = _read_json(batch_report_path)
    failure_manifest = _read_json(failure_manifest_path)
    resume_states = collect_resume_states(output_dir, options.resume_glob)

    summary = batch_report.get("summary", {}) if isinstance(batch_report, dict) else {}
    failed_files = failure_manifest.get("failed_files", []) if isinstance(failure_manifest, dict) else []
    completed_resume = sum(1 for item in resume_states if item.get("status") == "complete")
    failed_resume = sum(1 for item in resume_states if item.get("status") == "failed")
    active_resume = sum(1 for item in resume_states if item.get("status") in {"pending", "in_progress"})
    total_resume_chunks = sum(int(item.get("chunk_total", 0) or 0) for item in resume_states)
    completed_resume_chunks = sum(int(item.get("completed_chunks", 0) or 0) for item in resume_states)

    dashboard_status = "no_report"
    if batch_report:
        dashboard_status = batch_report.get("status", "unknown")
    if failed_files:
        dashboard_status = "attention_required"
    elif active_resume and dashboard_status == "success":
        dashboard_status = "resume_pending"

    dashboard = {
        "version": "1.1-lts-stage-09",
        "status": dashboard_status,
        "created_at": now_iso(),
        "output_dir": str(output_dir),
        "report_dir": str(report_dir),
        "batch_report": str(batch_report_path),
        "failure_manifest": str(failure_manifest_path),
        "summary": {
            "batch_status": batch_report.get("status", "missing") if isinstance(batch_report, dict) and batch_report else "missing",
            "total_files": summary.get("total_files", 0),
            "completed_files": summary.get("completed_files", 0),
            "success": summary.get("success", 0),
            "skipped": summary.get("skipped", 0),
            "failed": summary.get("failed", 0),
            "completion_rate_percent": summary.get("completion_rate_percent", 0),
            "success_rate_percent": summary.get("success_rate_percent", 0),
            "elapsed_hms": summary.get("elapsed_hms", "00:00:00"),
            "failed_manifest_count": len(failed_files),
            "resume_state_count": len(resume_states),
            "resume_complete": completed_resume,
            "resume_active": active_resume,
            "resume_failed": failed_resume,
            "resume_chunk_progress_percent": safe_percent(completed_resume_chunks, total_resume_chunks),
            "resume_chunks_completed": completed_resume_chunks,
            "resume_chunks_total": total_resume_chunks,
        },
        "failed_files": failed_files,
        "resume_states": resume_states,
    }

    if options.write_report:
        report_dir.mkdir(parents=True, exist_ok=True)
        json_path = report_dir / f"{DEFAULT_MONITOR_BASENAME}.json"
        md_path = report_dir / f"{DEFAULT_MONITOR_BASENAME}.md"
        dashboard["monitor_json"] = str(json_path)
        dashboard["monitor_md"] = str(md_path)
        save_json(json_path, dashboard)
        save_text(md_path, format_dashboard_markdown(dashboard))
    return dashboard


def format_dashboard_text(dashboard: dict) -> str:
    summary = dashboard.get("summary", {})
    lines = [
        "NTPE 1.1 LTS Batch Runtime Monitor",
        "====================================",
        f"status: {dashboard.get('status')}",
        f"batch_status: {summary.get('batch_status')}",
        f"files: {summary.get('success')} success / {summary.get('skipped')} skipped / {summary.get('failed')} failed / {summary.get('total_files')} total",
        f"completion_rate: {summary.get('completion_rate_percent')}%",
        f"success_rate: {summary.get('success_rate_percent')}%",
        f"elapsed: {summary.get('elapsed_hms', format_duration(0))}",
        f"failed_manifest_count: {summary.get('failed_manifest_count')}",
        f"resume_states: {summary.get('resume_state_count')} total / {summary.get('resume_complete')} complete / {summary.get('resume_active')} active / {summary.get('resume_failed')} failed",
        f"resume_chunks: {summary.get('resume_chunks_completed')} / {summary.get('resume_chunks_total')} ({summary.get('resume_chunk_progress_percent')}%)",
        f"report: {dashboard.get('batch_report')}",
        f"failure_manifest: {dashboard.get('failure_manifest')}",
    ]
    return "\n".join(lines) + "\n"


def format_dashboard_markdown(dashboard: dict) -> str:
    summary = dashboard.get("summary", {})
    lines = [
        "# NTPE 1.1 LTS Stage-09 Batch Runtime Monitor",
        "",
        f"- Status: {dashboard.get('status')}",
        f"- Batch Status: {summary.get('batch_status')}",
        f"- Created At: {dashboard.get('created_at')}",
        f"- Output Directory: `{dashboard.get('output_dir')}`",
        f"- Report Directory: `{dashboard.get('report_dir')}`",
        f"- Total Files: {summary.get('total_files')}",
        f"- Success / Skipped / Failed: {summary.get('success')} / {summary.get('skipped')} / {summary.get('failed')}",
        f"- Completion Rate: {summary.get('completion_rate_percent')}%",
        f"- Success Rate: {summary.get('success_rate_percent')}%",
        f"- Failed Manifest Count: {summary.get('failed_manifest_count')}",
        f"- Resume States: {summary.get('resume_state_count')}",
        f"- Resume Chunk Progress: {summary.get('resume_chunks_completed')} / {summary.get('resume_chunks_total')} ({summary.get('resume_chunk_progress_percent')}%)",
        "",
        "## Failed Files",
        "",
    ]
    failed_files = dashboard.get("failed_files", [])
    if failed_files:
        for item in failed_files:
            lines.append(f"- `{item.get('input', '')}` — {item.get('error', '')}")
    else:
        lines.append("- none")
    lines.extend(["", "## Resume States", "", "| Status | Input | Chunks | Progress | Updated |", "|---|---|---:|---:|---|"])
    for item in dashboard.get("resume_states", []):
        lines.append(
            f"| {item.get('status')} | `{item.get('input', '')}` | {item.get('completed_chunks', 0)} / {item.get('chunk_total', 0)} | {item.get('progress_percent', 0)}% | {item.get('updated_at', '')} |"
        )
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: Iterable[str] | None = None) -> BatchMonitorOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS Stage-09 batch resume dashboard / runtime monitor")
    parser.add_argument("output", nargs="?", default="output", help="batch output directory")
    parser.add_argument("--report-dir", default=None, help="report directory, defaults to output/reports")
    parser.add_argument("--failure-manifest", default=None, help="custom failure manifest filename/path")
    parser.add_argument("--resume-glob", default="*_resume_state.json", help="resume state glob pattern")
    parser.add_argument("--no-write-report", action="store_true", help="do not write monitor json/md reports")
    parser.add_argument("--quiet", action="store_true", help="do not print dashboard text")
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return BatchMonitorOptions(
        output_dir=Path(ns.output),
        report_dir=Path(ns.report_dir) if ns.report_dir else None,
        failure_manifest=Path(ns.failure_manifest) if ns.failure_manifest else None,
        resume_glob=ns.resume_glob,
        write_report=not ns.no_write_report,
        quiet=ns.quiet,
    )


def main(argv: Iterable[str] | None = None) -> int:
    try:
        options = parse_args(argv)
        dashboard = build_dashboard(options)
        if not options.quiet:
            print(format_dashboard_text(dashboard), end="")
        return 0
    except Exception as exc:
        print("NTPE 1.1 LTS Batch Runtime Monitor")
        print("====================================")
        print("status: failed")
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
