from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from core.translation_engine.utils import now_iso, save_json, save_text
DEFAULT_BATCH_REPORT_BASENAME = "Batch_Translation_Report"
DEFAULT_BATCH_FAILURE_BASENAME = "Batch_Failure_Manifest"


def safe_percent(part: int | float, whole: int | float) -> float:
    whole = float(whole or 0)
    if whole <= 0:
        return 0.0
    return round((float(part or 0) / whole) * 100, 2)

DEFAULT_HEARTBEAT_BASENAME = "Batch_Heartbeat"
DEFAULT_RECOVERY_PLAN_BASENAME = "Batch_Recovery_Plan"
DEFAULT_STALE_AFTER_SECONDS = 1800


@dataclass(frozen=True)
class LongRunRecoveryOptions:
    output_dir: Path
    report_dir: Path | None = None
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS
    write_report: bool = True
    quiet: bool = False


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"status": "unreadable", "error": str(exc), "path": str(path)}
    return data if isinstance(data, dict) else {}


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _age_seconds(value: str | None, reference: datetime | None = None) -> float | None:
    dt = _parse_iso(value)
    if not dt:
        return None
    reference = reference or datetime.now(timezone.utc)
    return max(0.0, (reference - dt).total_seconds())


def resolve_report_dir(output_dir: Path, report_dir: Path | None = None) -> Path:
    if report_dir is None:
        return output_dir / "reports"
    return report_dir if report_dir.is_absolute() else output_dir / report_dir


def heartbeat_path(report_dir: Path) -> Path:
    return report_dir / f"{DEFAULT_HEARTBEAT_BASENAME}.json"


def recovery_plan_path(report_dir: Path) -> Path:
    return report_dir / f"{DEFAULT_RECOVERY_PLAN_BASENAME}.json"


def write_heartbeat(
    report_dir: Path,
    *,
    status: str,
    current_file: str = "",
    current_index: int = 0,
    total_files: int = 0,
    completed_files: int = 0,
    message: str = "",
) -> dict:
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "1.1-lts-stage-10",
        "status": status,
        "updated_at": now_iso(),
        "current_file": current_file,
        "current_index": current_index,
        "total_files": total_files,
        "completed_files": completed_files,
        "progress_percent": safe_percent(completed_files, total_files),
        "message": message,
    }
    save_json(heartbeat_path(report_dir), payload)
    return payload


def collect_stale_resume_states(output_dir: Path, stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS) -> list[dict]:
    output_dir = Path(output_dir)
    stale: list[dict] = []
    for path in sorted(output_dir.rglob("*_resume_state.json")):
        data = _read_json(path)
        chunks = data.get("chunks", {}) if isinstance(data, dict) else {}
        total = int(data.get("chunk_total", len(chunks)) or len(chunks) or 0)
        completed = sum(1 for item in chunks.values() if isinstance(item, dict) and item.get("status") in {"success", "skipped"})
        failed = sum(1 for item in chunks.values() if isinstance(item, dict) and item.get("status") in {"failed", "qa_failed"})
        age = _age_seconds(data.get("updated_at"))
        is_incomplete = bool(total and completed < total)
        is_stale = age is not None and age >= max(0, stale_after_seconds)
        if failed or (is_incomplete and is_stale):
            stale.append({
                "path": str(path),
                "input": data.get("input", ""),
                "updated_at": data.get("updated_at", ""),
                "age_seconds": round(age, 3) if age is not None else None,
                "chunk_total": total,
                "completed_chunks": completed,
                "failed_chunks": failed,
                "progress_percent": safe_percent(completed, total),
                "reason": "failed_chunks" if failed else "stale_incomplete_resume",
            })
    return stale


def build_recovery_plan(options: LongRunRecoveryOptions, root: str | Path | None = None) -> dict:
    root_path = Path(root) if root else Path(__file__).resolve().parents[1]
    output_dir = options.output_dir if options.output_dir.is_absolute() else root_path / options.output_dir
    report_dir = resolve_report_dir(output_dir, options.report_dir)
    batch_report_path = report_dir / f"{DEFAULT_BATCH_REPORT_BASENAME}.json"
    failure_manifest_path = report_dir / f"{DEFAULT_BATCH_FAILURE_BASENAME}.json"
    hb_path = heartbeat_path(report_dir)

    batch_report = _read_json(batch_report_path)
    failure_manifest = _read_json(failure_manifest_path)
    heartbeat = _read_json(hb_path)
    failed_files = failure_manifest.get("failed_files", []) if isinstance(failure_manifest, dict) else []
    stale_resume_states = collect_stale_resume_states(output_dir, options.stale_after_seconds)

    actions: list[dict] = []
    if failed_files:
        actions.append({
            "type": "retry_failed_manifest",
            "command": "python ntpe_translate_batch.py input output --failed-only --continue-on-failure",
            "reason": f"{len(failed_files)} failed file(s) are recorded in the failure manifest.",
        })
    if stale_resume_states:
        actions.append({
            "type": "resume_stale_jobs",
            "command": "python ntpe_translate_batch.py input output --continue-on-failure",
            "reason": f"{len(stale_resume_states)} stale or failed resume state(s) were detected.",
        })
    if heartbeat and heartbeat.get("status") == "running":
        age = _age_seconds(heartbeat.get("updated_at"))
        if age is not None and age >= max(0, options.stale_after_seconds):
            actions.append({
                "type": "stale_heartbeat",
                "command": "python ntpe_batch_monitor.py output",
                "reason": f"Heartbeat has not been updated for {round(age, 3)} seconds.",
            })

    status = "recovery_required" if actions else "healthy"
    plan = {
        "version": "1.1-lts-stage-10",
        "status": status,
        "created_at": now_iso(),
        "output_dir": str(output_dir),
        "report_dir": str(report_dir),
        "batch_report": str(batch_report_path),
        "failure_manifest": str(failure_manifest_path),
        "heartbeat": str(hb_path),
        "summary": {
            "batch_status": batch_report.get("status", "missing") if batch_report else "missing",
            "heartbeat_status": heartbeat.get("status", "missing") if heartbeat else "missing",
            "failed_manifest_count": len(failed_files),
            "stale_resume_count": len(stale_resume_states),
            "action_count": len(actions),
            "stale_after_seconds": max(0, options.stale_after_seconds),
        },
        "actions": actions,
        "failed_files": failed_files,
        "stale_resume_states": stale_resume_states,
    }

    if options.write_report:
        report_dir.mkdir(parents=True, exist_ok=True)
        json_path = recovery_plan_path(report_dir)
        md_path = report_dir / f"{DEFAULT_RECOVERY_PLAN_BASENAME}.md"
        plan["recovery_plan_json"] = str(json_path)
        plan["recovery_plan_md"] = str(md_path)
        save_json(json_path, plan)
        save_text(md_path, format_recovery_plan_markdown(plan))
    return plan


def format_recovery_plan_text(plan: dict) -> str:
    summary = plan.get("summary", {})
    lines = [
        "NTPE 1.1 LTS Long-Run Recovery Monitor",
        "=========================================",
        f"status: {plan.get('status')}",
        f"batch_status: {summary.get('batch_status')}",
        f"heartbeat_status: {summary.get('heartbeat_status')}",
        f"failed_manifest_count: {summary.get('failed_manifest_count')}",
        f"stale_resume_count: {summary.get('stale_resume_count')}",
        f"action_count: {summary.get('action_count')}",
        f"recovery_plan: {plan.get('recovery_plan_json', '')}",
    ]
    for action in plan.get("actions", []):
        lines.append(f"action: {action.get('type')} | {action.get('command')}")
    return "\n".join(lines).strip() + "\n"


def format_recovery_plan_markdown(plan: dict) -> str:
    summary = plan.get("summary", {})
    lines = [
        "# NTPE 1.1 LTS Stage-10 Long-Run Recovery Plan",
        "",
        f"- Status: {plan.get('status')}",
        f"- Batch Status: {summary.get('batch_status')}",
        f"- Heartbeat Status: {summary.get('heartbeat_status')}",
        f"- Failed Manifest Count: {summary.get('failed_manifest_count')}",
        f"- Stale Resume Count: {summary.get('stale_resume_count')}",
        f"- Action Count: {summary.get('action_count')}",
        "",
        "## Recovery Actions",
        "",
    ]
    actions = plan.get("actions", [])
    if actions:
        for action in actions:
            lines.append(f"- `{action.get('type')}` — `{action.get('command')}` — {action.get('reason')}")
    else:
        lines.append("- none")
    lines.extend(["", "## Stale Resume States", "", "| Reason | Input | Chunks | Progress | Age Seconds |", "|---|---|---:|---:|---:|"])
    for item in plan.get("stale_resume_states", []):
        lines.append(
            f"| {item.get('reason')} | `{item.get('input', '')}` | {item.get('completed_chunks', 0)} / {item.get('chunk_total', 0)} | {item.get('progress_percent', 0)}% | {item.get('age_seconds', '')} |"
        )
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: Iterable[str] | None = None) -> LongRunRecoveryOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS Stage-10 long-run stability / auto recovery monitor")
    parser.add_argument("output", nargs="?", default="output", help="batch output directory")
    parser.add_argument("--report-dir", default=None, help="report directory, defaults to output/reports")
    parser.add_argument("--stale-after-seconds", type=int, default=DEFAULT_STALE_AFTER_SECONDS)
    parser.add_argument("--no-write-report", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return LongRunRecoveryOptions(
        output_dir=Path(ns.output),
        report_dir=Path(ns.report_dir) if ns.report_dir else None,
        stale_after_seconds=max(0, ns.stale_after_seconds),
        write_report=not ns.no_write_report,
        quiet=ns.quiet,
    )


def main(argv: Iterable[str] | None = None) -> int:
    try:
        options = parse_args(argv)
        plan = build_recovery_plan(options)
        if not options.quiet:
            print(format_recovery_plan_text(plan), end="")
        return 0 if plan.get("status") in {"healthy", "recovery_required"} else 1
    except Exception as exc:
        print("NTPE 1.1 LTS Long-Run Recovery Monitor")
        print("=========================================")
        print("status: failed")
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
