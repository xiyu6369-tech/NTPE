# =====================================================
# NTPE 1.2 Professional — Stage-18.9 Production Translation Integration
# Official production translation CLI entry.
# =====================================================
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.translation_runtime import TranslationRuntime
from lts.txt_translation_runtime import TxtTranslationOptions
from lts.batch_translation_runtime import BatchTranslationOptions

DEFAULT_MODEL = "meta/llama-3.3-70b-instruct"


def _resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def _print_result(title: str, result: dict) -> int:
    print(title)
    print("=" * len(title))
    print(f"status: {result.get('status', 'unknown')}")
    for key in ("input", "input_dir", "output", "output_dir", "chunk_total", "resume_state", "report_md", "failure_manifest"):
        if key in result:
            print(f"{key}: {result.get(key)}")
    if result.get("error"):
        print(f"error: {result.get('error')}")
    summary = result.get("summary")
    if isinstance(summary, dict):
        print(f"files: {summary.get('success', 0)} success / {summary.get('skipped', 0)} skipped / {summary.get('failed', 0)} failed / {summary.get('total_files', 0)} total")
        print(f"chunks: {summary.get('total_chunks', 0)}")
        print(f"elapsed: {summary.get('elapsed_hms', '00:00:00')}")
    return 0 if result.get("status") == "success" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="launcher_translate.py",
        description="NTPE 1.2 Professional official production translator",
    )
    sub = parser.add_subparsers(dest="command")

    txt = sub.add_parser("txt", help="translate one TXT file")
    txt.add_argument("input", help="input TXT file path")
    txt.add_argument("output", nargs="?", default="output", help="output directory")
    txt.add_argument("--chunk-size", type=int, default=1800)
    txt.add_argument("--model", default=DEFAULT_MODEL)
    txt.add_argument("--glossary", default=None)
    txt.add_argument("--character-memory", default=None)
    txt.add_argument("--max-retries", type=int, default=3)
    txt.add_argument("--retry-base-seconds", type=float, default=5.0)
    txt.add_argument("--qa-fail-policy", choices=("retry", "fail", "warn"), default="retry")
    txt.add_argument("--min-length-ratio", type=float, default=0.25)
    txt.add_argument("--max-korean-chars", type=int, default=3)
    txt.add_argument("--max-repeated-lines", type=int, default=2)
    txt.add_argument("--no-resume", action="store_true")
    txt.add_argument("--no-qa", action="store_true")
    txt.add_argument("--dry-run", action="store_true", help="build packages only; do not call NVIDIA API")

    batch = sub.add_parser("batch", help="translate all TXT files in a folder")
    batch.add_argument("input", nargs="?", default="input", help="input folder; default: input")
    batch.add_argument("output", nargs="?", default="output", help="output folder; default: output")
    batch.add_argument("--recursive", action="store_true")
    batch.add_argument("--chunk-size", type=int, default=1800)
    batch.add_argument("--model", default=DEFAULT_MODEL)
    batch.add_argument("--glossary", default=None)
    batch.add_argument("--character-memory", default=None)
    batch.add_argument("--max-retries", type=int, default=3)
    batch.add_argument("--retry-base-seconds", type=float, default=5.0)
    batch.add_argument("--qa-fail-policy", choices=("retry", "fail", "warn"), default="retry")
    batch.add_argument("--min-length-ratio", type=float, default=0.25)
    batch.add_argument("--max-korean-chars", type=int, default=3)
    batch.add_argument("--max-repeated-lines", type=int, default=2)
    batch.add_argument("--continue-on-failure", action="store_true")
    batch.add_argument("--auto-recovery", action="store_true")
    batch.add_argument("--heartbeat", action="store_true")
    batch.add_argument("--no-resume", action="store_true")
    batch.add_argument("--no-qa", action="store_true")
    batch.add_argument("--dry-run", action="store_true", help="build packages only; do not call NVIDIA API")

    doctor = sub.add_parser("doctor", help="check production translator environment")
    doctor.add_argument("--strict", action="store_true", help="fail when NVIDIA_API_KEY is missing")
    return parser


def run_doctor(strict: bool = False) -> int:
    print("NTPE Production Translator Doctor")
    print("=================================")
    checks = []
    checks.append(("project_root", ROOT.exists(), str(ROOT)))
    checks.append(("core_runtime", (ROOT / "core" / "translation_runtime").exists(), "core/translation_runtime"))
    checks.append(("lts_txt_runtime", (ROOT / "lts" / "txt_translation_runtime.py").exists(), "lts/txt_translation_runtime.py"))
    checks.append(("lts_batch_runtime", (ROOT / "lts" / "batch_translation_runtime.py").exists(), "lts/batch_translation_runtime.py"))
    checks.append(("input_dir", (ROOT / "input").exists(), "input"))
    checks.append(("output_dir", (ROOT / "output").exists(), "output"))
    api_ok = bool(os.environ.get("NVIDIA_API_KEY"))
    checks.append(("NVIDIA_API_KEY", api_ok or not strict, "set NVIDIA_API_KEY=你的Key" if not api_ok else "configured"))
    checks.append(("NTPE_API_TIMEOUT", True, os.environ.get("NTPE_API_TIMEOUT", "60")))
    checks.append(("NTPE_API_CONNECT_TIMEOUT", True, os.environ.get("NTPE_API_CONNECT_TIMEOUT", "10")))
    checks.append(("NTPE_TRANSLATE_DEBUG", True, os.environ.get("NTPE_TRANSLATE_DEBUG", "off")))
    failed = False
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        print(f"{name:<24} {status:<5} {detail}")
        failed = failed or not ok
    return 1 if failed else 0


def run_txt(args: argparse.Namespace) -> int:
    runtime = TranslationRuntime(root=ROOT)
    options = TxtTranslationOptions(
        input_path=_resolve(args.input),
        output_dir=_resolve(args.output),
        chunk_size=max(300, args.chunk_size),
        model=args.model,
        resume=not args.no_resume,
        dry_run=args.dry_run,
        max_retries=max(0, args.max_retries),
        retry_base_seconds=max(0.0, args.retry_base_seconds),
        glossary_path=Path(args.glossary) if args.glossary else None,
        character_memory_path=Path(args.character_memory) if args.character_memory else None,
        qa_enabled=not args.no_qa,
        qa_fail_policy=args.qa_fail_policy,
        min_length_ratio=max(0.0, args.min_length_ratio),
        max_korean_chars=max(0, args.max_korean_chars),
        max_repeated_lines=max(0, args.max_repeated_lines),
    )
    return _print_result("NTPE Production TXT Translation", runtime.translate_txt(options))


def run_batch(args: argparse.Namespace) -> int:
    runtime = TranslationRuntime(root=ROOT)
    options = BatchTranslationOptions(
        input_dir=_resolve(args.input),
        output_dir=_resolve(args.output),
        recursive=args.recursive,
        chunk_size=max(300, args.chunk_size),
        model=args.model,
        resume=not args.no_resume,
        dry_run=args.dry_run,
        max_retries=max(0, args.max_retries),
        retry_base_seconds=max(0.0, args.retry_base_seconds),
        glossary_path=Path(args.glossary) if args.glossary else None,
        character_memory_path=Path(args.character_memory) if args.character_memory else None,
        qa_enabled=not args.no_qa,
        qa_fail_policy=args.qa_fail_policy,
        min_length_ratio=max(0.0, args.min_length_ratio),
        max_korean_chars=max(0, args.max_korean_chars),
        max_repeated_lines=max(0, args.max_repeated_lines),
        continue_on_failure=args.continue_on_failure,
        auto_recovery=args.auto_recovery,
        heartbeat=args.heartbeat,
    )
    return _print_result("NTPE Production Batch Translation", runtime.translate_batch(options))


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command is None:
        parser.print_help()
        print("\n常用指令：")
        print("  set NVIDIA_API_KEY=你的Key")
        print("  python launcher_translate.py batch input output")
        print("  python launcher_translate.py txt input\\novel.txt output")
        return 0
    if args.command == "doctor":
        return run_doctor(strict=args.strict)
    if args.command == "txt":
        return run_txt(args)
    if args.command == "batch":
        return run_batch(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
