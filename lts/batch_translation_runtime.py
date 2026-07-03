from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

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


def _write_batch_markdown(report: dict, path: Path) -> None:
    lines = [
        "# NTPE 1.1 LTS Stage-06 Batch Translation Report",
        "",
        f"- Status: {report.get('status')}",
        f"- Started At: {report.get('started_at')}",
        f"- Completed At: {report.get('completed_at')}",
        f"- Input Directory: `{report.get('input_dir')}`",
        f"- Output Directory: `{report.get('output_dir')}`",
        f"- Total Files: {report['summary'].get('total_files')}",
        f"- Success: {report['summary'].get('success')}",
        f"- Skipped: {report['summary'].get('skipped')}",
        f"- Failed: {report['summary'].get('failed')}",
        f"- Total Chunks: {report['summary'].get('total_chunks')}",
        f"- Elapsed Seconds: {report['summary'].get('elapsed_seconds')}",
        "",
        "## Files",
        "",
        "| # | Status | Input | Output | Chunks | Error |",
        "|---:|---|---|---|---:|---|",
    ]
    for record in report.get("files", []):
        lines.append(
            f"| {record.get('index')} | {record.get('status')} | `{record.get('input')}` | `{record.get('output', '')}` | {record.get('chunk_total', 0)} | {record.get('error', '')} |"
        )
    save_text(path, "\n".join(lines).strip() + "\n")


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
    records: list[dict] = []
    summary = {
        "total_files": len(files),
        "success": 0,
        "skipped": 0,
        "failed": 0,
        "total_chunks": 0,
    }

    for index, input_file in enumerate(files, start=1):
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
            record.update({"status": "skipped", "chunk_total": 0, "completed_at": now_iso()})
            summary["skipped"] += 1
            records.append(record)
            continue

        txt_options = build_txt_options(input_file, per_file_output_dir, options)
        try:
            result = translate_txt(txt_options, root=root_path)
        except Exception as exc:
            record.update({"status": "failed", "error": str(exc), "completed_at": now_iso()})
            summary["failed"] += 1
            records.append(record)
            break

        status = result.get("status", "failed")
        record.update({
            "status": status,
            "output": result.get("output", str(final_output)),
            "chunk_total": result.get("chunk_total", 0),
            "resume_state": result.get("resume_state", ""),
            "completed_at": now_iso(),
        })
        summary["total_chunks"] += int(result.get("chunk_total", 0) or 0)
        if status == "success":
            summary["success"] += 1
        else:
            summary["failed"] += 1
            record["error"] = result.get("error", "batch item failed")
            records.append(record)
            break
        records.append(record)

    summary["elapsed_seconds"] = _elapsed_seconds(started)
    status = "success" if summary["failed"] == 0 else "failed"
    completed_at = now_iso()
    report = {
        "version": "1.1-lts-stage-06",
        "status": status,
        "started_at": started_at,
        "completed_at": completed_at,
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "recursive": options.recursive,
        "skip_completed": options.skip_completed,
        "dry_run": options.dry_run,
        "summary": summary,
        "files": records,
    }
    json_path = report_dir / f"{DEFAULT_BATCH_REPORT_BASENAME}.json"
    md_path = report_dir / f"{DEFAULT_BATCH_REPORT_BASENAME}.md"
    save_json(json_path, report)
    _write_batch_markdown(report, md_path)
    report["report_json"] = str(json_path)
    report["report_md"] = str(md_path)
    save_json(json_path, report)
    return report


def parse_args(argv: Iterable[str] | None = None) -> BatchTranslationOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS Stage-06 batch folder TXT translation")
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
        print(f"report: {result.get('report_md', '')}")
        return 0 if result.get("status") == "success" else 1
    except Exception as exc:
        print("NTPE 1.1 LTS Batch Folder Translation")
        print("======================================")
        print("status: failed")
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
