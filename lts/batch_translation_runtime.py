from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from core.translation_engine.utils import now_iso, save_json, save_text
from lts.txt_translation_runtime import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHARACTER_MEMORY,
    DEFAULT_MAX_KOREAN_CHARS,
    DEFAULT_MAX_REPEATED_LINES,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MIN_LENGTH_RATIO,
    DEFAULT_MODEL,
    DEFAULT_RETRY_BASE_SECONDS,
    QA_FAIL_POLICIES,
    TxtTranslationOptions,
    translate_txt,
)


DEFAULT_BATCH_REPORT_BASENAME = "Batch_Translation_Report"
DEFAULT_BATCH_FAILURE_BASENAME = "Batch_Failure_Manifest"


def format_duration(seconds: float | int | None) -> str:
    total = max(0, int(seconds or 0))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def safe_percent(part: int | float, whole: int | float) -> float:
    whole = float(whole or 0)
    if whole <= 0:
        return 0.0
    return round((float(part or 0) / whole) * 100, 2)


def estimate_remaining_seconds(completed: int, total: int, elapsed_seconds: float) -> float | None:
    if completed <= 0 or total <= 0 or completed >= total:
        return 0.0 if completed >= total else None
    average = elapsed_seconds / completed
    return round(average * (total - completed), 3)


@dataclass(frozen=True)
class BatchProgressSnapshot:
    index: int
    total: int
    status: str
    input_name: str
    success: int
    skipped: int
    failed: int
    elapsed_seconds: float
    eta_seconds: float | None

    @property
    def completed(self) -> int:
        return self.success + self.skipped + self.failed

    @property
    def percent(self) -> float:
        return safe_percent(self.completed, self.total)


def format_progress_line(snapshot: BatchProgressSnapshot) -> str:
    eta = format_duration(snapshot.eta_seconds) if snapshot.eta_seconds is not None else "--:--:--"
    return (
        f"[{snapshot.completed}/{snapshot.total} {snapshot.percent:.2f}%] "
        f"{snapshot.status}: {snapshot.input_name} | "
        f"success={snapshot.success} skipped={snapshot.skipped} failed={snapshot.failed} | "
        f"elapsed={format_duration(snapshot.elapsed_seconds)} eta={eta}"
    )


class BatchProgressReporter:
    def __init__(self, enabled: bool = True, sink: Callable[[str], None] | None = None) -> None:
        self.enabled = enabled
        self.sink = sink or print
        self.lines: list[str] = []

    def emit(self, snapshot: BatchProgressSnapshot) -> None:
        line = format_progress_line(snapshot)
        self.lines.append(line)
        if self.enabled:
            self.sink(line)


@dataclass(frozen=True)
class BatchTranslationOptions:
    input_dir: Path
    output_dir: Path
    recursive: bool = False
    skip_completed: bool = True
    output_suffix: str = "_zh"
    chunk_size: int = DEFAULT_CHUNK_SIZE
    model: str = DEFAULT_MODEL
    project_name: str = "NTPE Batch Novel Translation"
    resume: bool = True
    dry_run: bool = False
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_base_seconds: float = DEFAULT_RETRY_BASE_SECONDS
    glossary_path: Path | None = None
    character_memory_path: Path | None = None
    strict_lock_terms: bool = True
    qa_enabled: bool = True
    qa_fail_policy: str = "retry"
    min_length_ratio: float = DEFAULT_MIN_LENGTH_RATIO
    max_korean_chars: int = DEFAULT_MAX_KOREAN_CHARS
    max_repeated_lines: int = DEFAULT_MAX_REPEATED_LINES
    output_formatter_enabled: bool = True
    taiwan_traditional_normalization: bool = True
    report_dir: Path | None = None
    progress: bool = True
    continue_on_failure: bool = False
    failed_only: bool = False
    failed_manifest: Path | None = None


def natural_sort_key(path: Path) -> list[object]:
    text = str(path).replace("\\", "/").lower()
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", text)]


def scan_txt_files(input_dir: str | Path, recursive: bool = False) -> list[Path]:
    root = Path(input_dir)
    if not root.exists():
        raise FileNotFoundError(f"input directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"input path is not a directory: {root}")
    pattern = "**/*.txt" if recursive else "*.txt"
    return sorted((p for p in root.glob(pattern) if p.is_file()), key=natural_sort_key)


def get_output_path_for_input(input_file: Path, input_dir: Path, output_dir: Path, suffix: str = "_zh") -> Path:
    try:
        relative = input_file.relative_to(input_dir)
    except ValueError:
        relative = Path(input_file.name)
    return (output_dir / relative).with_name(f"{relative.stem}{suffix}{relative.suffix}")


def build_txt_options(input_file: Path, per_file_output_dir: Path, options: BatchTranslationOptions) -> TxtTranslationOptions:
    return TxtTranslationOptions(
        input_path=input_file,
        output_dir=per_file_output_dir,
        chunk_size=options.chunk_size,
        model=options.model,
        project_name=options.project_name,
        resume=options.resume,
        dry_run=options.dry_run,
        max_retries=max(0, options.max_retries),
        retry_base_seconds=max(0.0, options.retry_base_seconds),
        glossary_path=options.glossary_path,
        character_memory_path=options.character_memory_path or Path(DEFAULT_CHARACTER_MEMORY),
        strict_lock_terms=options.strict_lock_terms,
        qa_enabled=options.qa_enabled,
        qa_fail_policy=options.qa_fail_policy,
        min_length_ratio=max(0.0, options.min_length_ratio),
        max_korean_chars=max(0, options.max_korean_chars),
        max_repeated_lines=max(0, options.max_repeated_lines),
        output_formatter_enabled=options.output_formatter_enabled,
        taiwan_traditional_normalization=options.taiwan_traditional_normalization,
    )


def _elapsed_seconds(start: float) -> float:
    return round(time.time() - start, 3)


def summarize_txt_result(result: dict) -> dict:
    records = result.get("records", []) if isinstance(result, dict) else []
    provider_attempts = 0
    qa_attempts = 0
    qa_retry_count = 0
    qa_issue_count = 0
    korean_residue_issues = 0
    skipped_chunks = 0
    failed_chunks = 0
    for record in records:
        provider_attempts += int(record.get("attempt", 0) or 0)
        qa_attempt = int(record.get("qa_attempt", 0) or 0)
        qa_attempts += qa_attempt
        if qa_attempt > 1:
            qa_retry_count += qa_attempt - 1
        if record.get("status") == "skipped":
            skipped_chunks += 1
        if record.get("status") in {"failed", "qa_failed"}:
            failed_chunks += 1
        qa = record.get("qa") or {}
        for issue in qa.get("issues", []) if isinstance(qa, dict) else []:
            qa_issue_count += 1
            if issue.get("code") == "KOREAN_RESIDUE":
                korean_residue_issues += 1
    return {
        "provider_attempts": provider_attempts,
        "provider_retry_count": max(0, provider_attempts - len(records)),
        "qa_attempts": qa_attempts,
        "qa_retry_count": qa_retry_count,
        "qa_issue_count": qa_issue_count,
        "korean_residue_issues": korean_residue_issues,
        "skipped_chunks": skipped_chunks,
        "failed_chunks": failed_chunks,
    }


def _write_batch_markdown(report: dict, path: Path) -> None:
    summary = report.get("summary", {})
    lines = [
        "# NTPE 1.1 LTS Stage-08 Batch Progress / Summary Report" if report.get("version") == "1.1-lts-stage-08" else "# NTPE 1.1 LTS Stage-07 Batch Progress / Summary Report",
        "",
        f"- Status: {report.get('status')}",
        f"- Version: {report.get('version')}",
        f"- Started At: {report.get('started_at')}",
        f"- Completed At: {report.get('completed_at')}",
        f"- Input Directory: `{report.get('input_dir')}`",
        f"- Output Directory: `{report.get('output_dir')}`",
        f"- Total Files: {summary.get('total_files')}",
        f"- Completed Files: {summary.get('completed_files')}",
        f"- Success: {summary.get('success')}",
        f"- Skipped: {summary.get('skipped')}",
        f"- Failed: {summary.get('failed')}",
        f"- Success Rate: {summary.get('success_rate_percent')}%",
        f"- Total Chunks: {summary.get('total_chunks')}",
        f"- Provider Retries: {summary.get('provider_retry_count')}",
        f"- QA Retries: {summary.get('qa_retry_count')}",
        f"- QA Issues: {summary.get('qa_issue_count')}",
        f"- Korean Residue Issues: {summary.get('korean_residue_issues')}",
        f"- Elapsed: {summary.get('elapsed_hms')} ({summary.get('elapsed_seconds')} seconds)",
        f"- Average Seconds / File: {summary.get('average_seconds_per_file')}",
        f"- Average Chunks / File: {summary.get('average_chunks_per_file')}",
        "",
        "## Progress Log",
        "",
    ]
    progress_log = report.get("progress_log", [])
    if progress_log:
        lines.extend(f"- {line}" for line in progress_log)
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Files",
        "",
        "| # | Status | Input | Output | Chunks | Attempts | QA Retries | Error |",
        "|---:|---|---|---|---:|---:|---:|---|",
    ])
    for record in report.get("files", []):
        metrics = record.get("metrics", {})
        lines.append(
            f"| {record.get('index')} | {record.get('status')} | `{record.get('input')}` | `{record.get('output', '')}` | "
            f"{record.get('chunk_total', 0)} | {metrics.get('provider_attempts', 0)} | {metrics.get('qa_retry_count', 0)} | {record.get('error', '')} |"
        )
    save_text(path, "\n".join(lines).strip() + "\n")


def _emit_progress(
    reporter: BatchProgressReporter,
    *,
    index: int,
    total: int,
    status: str,
    input_name: str,
    summary: dict,
    started: float,
) -> None:
    completed = int(summary.get("success", 0)) + int(summary.get("skipped", 0)) + int(summary.get("failed", 0))
    elapsed = _elapsed_seconds(started)
    eta = estimate_remaining_seconds(completed, total, elapsed)
    reporter.emit(BatchProgressSnapshot(
        index=index,
        total=total,
        status=status,
        input_name=input_name,
        success=int(summary.get("success", 0)),
        skipped=int(summary.get("skipped", 0)),
        failed=int(summary.get("failed", 0)),
        elapsed_seconds=elapsed,
        eta_seconds=eta,
    ))


def resolve_failed_manifest_path(report_dir: Path, options: BatchTranslationOptions) -> Path:
    if options.failed_manifest:
        return options.failed_manifest if options.failed_manifest.is_absolute() else report_dir.parent / options.failed_manifest
    return report_dir / f"{DEFAULT_BATCH_FAILURE_BASENAME}.json"


def write_failure_manifest(report: dict, path: Path) -> None:
    failed_records = [record for record in report.get("files", []) if record.get("status") == "failed"]
    payload = {
        "version": "1.1-lts-stage-08",
        "status": "failed" if failed_records else "success",
        "created_at": now_iso(),
        "input_dir": report.get("input_dir"),
        "output_dir": report.get("output_dir"),
        "failed_count": len(failed_records),
        "failed_files": failed_records,
    }
    save_json(path, payload)


def load_failed_manifest(path: str | Path) -> set[str]:
    path = Path(path)
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return set()
    failed: set[str] = set()
    for record in data.get("failed_files", []) if isinstance(data, dict) else []:
        input_path = record.get("input") if isinstance(record, dict) else None
        if input_path:
            failed.add(str(input_path))
    return failed


def filter_failed_only(files: list[Path], report_dir: Path, options: BatchTranslationOptions, input_dir: Path) -> list[Path]:
    manifest_path = resolve_failed_manifest_path(report_dir, options)
    failed_paths = load_failed_manifest(manifest_path)
    if not failed_paths:
        return []
    normalized = {str(Path(item)) for item in failed_paths}
    return [path for path in files if str(path) in normalized or str(path.relative_to(input_dir)) in normalized or path.name in normalized]


def translate_batch(options: BatchTranslationOptions, root: str | Path | None = None) -> dict:
    root_path = Path(root) if root else Path(__file__).resolve().parents[1]
    input_dir = options.input_dir if options.input_dir.is_absolute() else root_path / options.input_dir
    output_dir = options.output_dir if options.output_dir.is_absolute() else root_path / options.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir = options.report_dir if options.report_dir else output_dir / "reports"
    report_dir = report_dir if report_dir.is_absolute() else root_path / report_dir
    report_dir.mkdir(parents=True, exist_ok=True)

    started = time.time()
    started_at = now_iso()
    files = scan_txt_files(input_dir, recursive=options.recursive)
    if options.failed_only:
        files = filter_failed_only(files, report_dir, options, input_dir)
    records: list[dict] = []
    reporter = BatchProgressReporter(enabled=options.progress)
    summary = {
        "total_files": len(files),
        "completed_files": 0,
        "success": 0,
        "skipped": 0,
        "failed": 0,
        "total_chunks": 0,
        "provider_attempts": 0,
        "provider_retry_count": 0,
        "qa_attempts": 0,
        "qa_retry_count": 0,
        "qa_issue_count": 0,
        "korean_residue_issues": 0,
        "skipped_chunks": 0,
        "failed_chunks": 0,
        "continue_on_failure": options.continue_on_failure,
        "failed_only": options.failed_only,
    }

    for index, input_file in enumerate(files, start=1):
        _emit_progress(reporter, index=index, total=len(files), status="start", input_name=input_file.name, summary=summary, started=started)
        final_output = get_output_path_for_input(input_file, input_dir, output_dir, options.output_suffix)
        per_file_output_dir = final_output.parent
        per_file_output_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "index": index,
            "total": len(files),
            "input": str(input_file),
            "output": str(final_output),
            "started_at": now_iso(),
        }

        if options.skip_completed and final_output.exists() and final_output.read_text(encoding="utf-8", errors="ignore").strip():
            record.update({"status": "skipped", "chunk_total": 0, "completed_at": now_iso(), "metrics": {}})
            summary["skipped"] += 1
            summary["completed_files"] += 1
            records.append(record)
            _emit_progress(reporter, index=index, total=len(files), status="skipped", input_name=input_file.name, summary=summary, started=started)
            continue

        txt_options = build_txt_options(input_file, per_file_output_dir, options)
        try:
            result = translate_txt(txt_options, root=root_path)
        except Exception as exc:
            record.update({"status": "failed", "error": str(exc), "completed_at": now_iso(), "metrics": {}})
            summary["failed"] += 1
            summary["completed_files"] += 1
            records.append(record)
            _emit_progress(reporter, index=index, total=len(files), status="failed", input_name=input_file.name, summary=summary, started=started)
            if not options.continue_on_failure:
                break
            continue

        status = result.get("status", "failed")
        metrics = summarize_txt_result(result)
        record.update({
            "status": status,
            "output": result.get("output", str(final_output)),
            "chunk_total": result.get("chunk_total", 0),
            "resume_state": result.get("resume_state", ""),
            "completed_at": now_iso(),
            "metrics": metrics,
        })
        summary["total_chunks"] += int(result.get("chunk_total", 0) or 0)
        for key in ("provider_attempts", "provider_retry_count", "qa_attempts", "qa_retry_count", "qa_issue_count", "korean_residue_issues", "skipped_chunks", "failed_chunks"):
            summary[key] += int(metrics.get(key, 0) or 0)
        if status == "success":
            summary["success"] += 1
            summary["completed_files"] += 1
            records.append(record)
            _emit_progress(reporter, index=index, total=len(files), status="success", input_name=input_file.name, summary=summary, started=started)
        else:
            summary["failed"] += 1
            summary["completed_files"] += 1
            record["error"] = result.get("error", "batch item failed")
            records.append(record)
            _emit_progress(reporter, index=index, total=len(files), status="failed", input_name=input_file.name, summary=summary, started=started)
            if not options.continue_on_failure:
                break
            continue

    summary["elapsed_seconds"] = _elapsed_seconds(started)
    summary["elapsed_hms"] = format_duration(summary["elapsed_seconds"])
    summary["success_rate_percent"] = safe_percent(summary["success"], max(1, summary["total_files"] - summary["skipped"]))
    summary["completion_rate_percent"] = safe_percent(summary["completed_files"], summary["total_files"])
    summary["average_seconds_per_file"] = round(summary["elapsed_seconds"] / summary["completed_files"], 3) if summary["completed_files"] else 0.0
    summary["average_chunks_per_file"] = round(summary["total_chunks"] / summary["success"], 3) if summary["success"] else 0.0
    status = "success" if summary["failed"] == 0 else "partial_success" if options.continue_on_failure and summary["success"] > 0 else "failed"
    completed_at = now_iso()
    report = {
        "version": "1.1-lts-stage-08" if (options.continue_on_failure or options.failed_only) else "1.1-lts-stage-07",
        "status": status,
        "started_at": started_at,
        "completed_at": completed_at,
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "recursive": options.recursive,
        "skip_completed": options.skip_completed,
        "dry_run": options.dry_run,
        "continue_on_failure": options.continue_on_failure,
        "failed_only": options.failed_only,
        "summary": summary,
        "progress_log": reporter.lines,
        "files": records,
    }
    json_path = report_dir / f"{DEFAULT_BATCH_REPORT_BASENAME}.json"
    md_path = report_dir / f"{DEFAULT_BATCH_REPORT_BASENAME}.md"
    save_json(json_path, report)
    _write_batch_markdown(report, md_path)
    report["report_json"] = str(json_path)
    report["report_md"] = str(md_path)
    failure_manifest_path = resolve_failed_manifest_path(report_dir, options)
    report["failure_manifest"] = str(failure_manifest_path)
    write_failure_manifest(report, failure_manifest_path)
    save_json(json_path, report)
    return report


def parse_args(argv: Iterable[str] | None = None) -> BatchTranslationOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS Stage-08 batch folder TXT translation with failure recovery")
    parser.add_argument("input", help="input folder containing TXT files")
    parser.add_argument("output", nargs="?", default="output", help="output directory")
    parser.add_argument("--recursive", action="store_true", help="scan TXT files recursively")
    parser.add_argument("--no-skip-completed", action="store_true", help="do not skip existing non-empty translated files")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--project-name", default="NTPE Batch Novel Translation")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--retry-base-seconds", type=float, default=DEFAULT_RETRY_BASE_SECONDS)
    parser.add_argument("--glossary", dest="glossary_path", default=None)
    parser.add_argument("--character-memory", dest="character_memory_path", default=None)
    parser.add_argument("--no-strict-lock-terms", action="store_true")
    parser.add_argument("--no-qa", action="store_true")
    parser.add_argument("--qa-fail-policy", choices=QA_FAIL_POLICIES, default="retry")
    parser.add_argument("--min-length-ratio", type=float, default=DEFAULT_MIN_LENGTH_RATIO)
    parser.add_argument("--max-korean-chars", type=int, default=DEFAULT_MAX_KOREAN_CHARS)
    parser.add_argument("--max-repeated-lines", type=int, default=DEFAULT_MAX_REPEATED_LINES)
    parser.add_argument("--no-output-formatter", action="store_true")
    parser.add_argument("--no-taiwan-normalization", action="store_true")
    parser.add_argument("--report-dir", default=None, help="optional batch report directory")
    parser.add_argument("--quiet-progress", action="store_true", help="disable live batch progress lines")
    parser.add_argument("--continue-on-failure", action="store_true", help="continue translating remaining files after a file fails")
    parser.add_argument("--failed-only", action="store_true", help="translate only files listed in the previous failure manifest")
    parser.add_argument("--failed-manifest", default=None, help="custom failure manifest path for failed-only/recovery runs")
    parser.add_argument("--dry-run", action="store_true", help="build prompt packages without provider calls")
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return BatchTranslationOptions(
        input_dir=Path(ns.input),
        output_dir=Path(ns.output),
        recursive=ns.recursive,
        skip_completed=not ns.no_skip_completed,
        chunk_size=max(300, ns.chunk_size),
        model=ns.model,
        project_name=ns.project_name,
        resume=not ns.no_resume,
        dry_run=ns.dry_run,
        max_retries=max(0, ns.max_retries),
        retry_base_seconds=max(0.0, ns.retry_base_seconds),
        glossary_path=Path(ns.glossary_path) if ns.glossary_path else None,
        character_memory_path=Path(ns.character_memory_path) if ns.character_memory_path else None,
        strict_lock_terms=not ns.no_strict_lock_terms,
        qa_enabled=not ns.no_qa,
        qa_fail_policy=ns.qa_fail_policy,
        min_length_ratio=max(0.0, ns.min_length_ratio),
        max_korean_chars=max(0, ns.max_korean_chars),
        max_repeated_lines=max(0, ns.max_repeated_lines),
        output_formatter_enabled=not ns.no_output_formatter,
        taiwan_traditional_normalization=not ns.no_taiwan_normalization,
        report_dir=Path(ns.report_dir) if ns.report_dir else None,
        progress=not ns.quiet_progress,
        continue_on_failure=ns.continue_on_failure,
        failed_only=ns.failed_only,
        failed_manifest=Path(ns.failed_manifest) if ns.failed_manifest else None,
    )


def main(argv: Iterable[str] | None = None) -> int:
    try:
        options = parse_args(argv)
        result = translate_batch(options)
        print("NTPE 1.1 LTS Batch Folder Translation")
        print("======================================")
        print(f"status: {result['status']}")
        print(f"input_dir: {result.get('input_dir', '')}")
        print(f"output_dir: {result.get('output_dir', '')}")
        print(f"files: {result['summary'].get('success', 0)} success / {result['summary'].get('skipped', 0)} skipped / {result['summary'].get('failed', 0)} failed / {result['summary'].get('total_files', 0)} total")
        print(f"chunks: {result['summary'].get('total_chunks', 0)}")
        print(f"elapsed: {result['summary'].get('elapsed_hms', '00:00:00')}")
        print(f"success_rate: {result['summary'].get('success_rate_percent', 0)}%")
        print(f"report: {result.get('report_md', '')}")
        print(f"failure_manifest: {result.get('failure_manifest', '')}")
        return 0 if result.get("status") == "success" else 1
    except Exception as exc:
        print("NTPE 1.1 LTS Batch Folder Translation")
        print("======================================")
        print("status: failed")
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
