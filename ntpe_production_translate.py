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

from ntpe_literary_regression import LiteraryRegressionOptions, discover_test_sets, ensure_literary_structure, run_literary_regression
from ntpe_literary_evaluation import evaluate_stage_outputs

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
    txt.add_argument("--chunk-size", type=int, default=None)
    txt.add_argument("--speed", choices=("fast", "balanced", "quality"), default=os.environ.get("NTPE_TRANSLATION_SPEED", "balanced"))
    txt.add_argument("--model", default=DEFAULT_MODEL)
    txt.add_argument("--fallback-models", default=os.environ.get("NTPE_FALLBACK_MODELS", ""), help="comma-separated fallback NVIDIA model IDs")
    txt.add_argument("--glossary", default=None)
    txt.add_argument("--character-memory", default=None)
    txt.add_argument("--max-retries", type=int, default=3)
    txt.add_argument("--provider-attempts", type=int, default=None, help="total provider request attempts; overrides speed-profile default")
    txt.add_argument("--retry-base-seconds", type=float, default=5.0)
    txt.add_argument("--qa-fail-policy", choices=("retry", "fail", "warn"), default="retry")
    txt.add_argument("--min-length-ratio", type=float, default=0.25)
    txt.add_argument("--max-korean-chars", type=int, default=3)
    txt.add_argument("--max-repeated-lines", type=int, default=2)
    txt.add_argument("--no-resume", action="store_true")
    txt.add_argument("--no-qa", action="store_true")
    txt.add_argument("--profile", choices=("fast", "balanced", "novel", "literary", "quality", "premium"), default=os.environ.get("NTPE_TRANSLATION_PROFILE", "literary"))
    txt.add_argument("--simplified-chinese-policy", choices=("normalize", "warn", "fail"), default=os.environ.get("NTPE_SIMPLIFIED_CHINESE_POLICY", "normalize"))
    txt.add_argument("--api-timeout", type=int, default=None, help="provider read timeout upper bound in seconds")
    txt.add_argument("--api-connect-timeout", type=int, default=None, help="provider connect timeout in seconds")
    txt.add_argument("--dry-run", action="store_true", help="build packages only; do not call NVIDIA API")
    txt.add_argument("--no-progress", action="store_true", help="disable live NTPE progress messages")

    batch = sub.add_parser("batch", help="translate all TXT files in a folder")
    batch.add_argument("input", nargs="?", default="input", help="input folder; default: input")
    batch.add_argument("output", nargs="?", default="output", help="output folder; default: output")
    batch.add_argument("--recursive", action="store_true")
    batch.add_argument("--chunk-size", type=int, default=None)
    batch.add_argument("--speed", choices=("fast", "balanced", "quality"), default=os.environ.get("NTPE_TRANSLATION_SPEED", "balanced"))
    batch.add_argument("--model", default=DEFAULT_MODEL)
    batch.add_argument("--fallback-models", default=os.environ.get("NTPE_FALLBACK_MODELS", ""), help="comma-separated fallback NVIDIA model IDs")
    batch.add_argument("--glossary", default=None)
    batch.add_argument("--character-memory", default=None)
    batch.add_argument("--max-retries", type=int, default=3)
    batch.add_argument("--provider-attempts", type=int, default=None, help="total provider request attempts; overrides speed-profile default")
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
    batch.add_argument("--profile", choices=("fast", "balanced", "novel", "literary", "quality", "premium"), default=os.environ.get("NTPE_TRANSLATION_PROFILE", "literary"))
    batch.add_argument("--simplified-chinese-policy", choices=("normalize", "warn", "fail"), default=os.environ.get("NTPE_SIMPLIFIED_CHINESE_POLICY", "normalize"))
    batch.add_argument("--api-timeout", type=int, default=None, help="provider read timeout upper bound in seconds")
    batch.add_argument("--api-connect-timeout", type=int, default=None, help="provider connect timeout in seconds")
    batch.add_argument("--dry-run", action="store_true", help="build packages only; do not call NVIDIA API")
    batch.add_argument("--no-progress", action="store_true", help="disable live NTPE progress messages")

    regression = sub.add_parser("regression", help="run literary regression corpus under tests/literary")
    regression.add_argument(
        "--set",
        dest="sets",
        action="append",
        choices=("Test_Set_0", "Test_Set_A", "Test_Set_B", "smoke", "golden", "regression", "Smoke_Set", "Golden_Set", "Regression_Set"),
        help="run one test set; aliases: smoke/golden/regression",
    )
    regression.add_argument("--stage", default=os.environ.get("NTPE_PS_STAGE", "PS-03"), help="output archive stage name under tests/literary/outputs")
    regression.add_argument("--profile", choices=("fast", "balanced", "novel", "literary", "quality", "premium"), default=os.environ.get("NTPE_TRANSLATION_PROFILE", "literary"))
    regression.add_argument("--chunk-size", type=int, default=None)
    regression.add_argument("--speed", choices=("fast", "balanced", "quality"), default=os.environ.get("NTPE_TRANSLATION_SPEED", "balanced"))
    regression.add_argument("--model", default=DEFAULT_MODEL)
    regression.add_argument("--fallback-models", default=os.environ.get("NTPE_FALLBACK_MODELS", ""), help="comma-separated fallback NVIDIA model IDs")
    regression.add_argument("--dry-run", action="store_true", help="build prompt packages and reports without calling NVIDIA API")
    regression.add_argument("--overwrite", action="store_true", help="clear the stage output folder before running")
    regression.add_argument("--no-resume", action="store_true", help="disable chunk resume for this regression run")
    regression.add_argument("--no-evaluate", action="store_true", help="skip PS-03 quality evaluation report")
    regression.add_argument("--previous-stage", default=None, help="optional previous stage folder for diff report")
    regression.add_argument("--max-retries", type=int, default=3)
    regression.add_argument("--provider-attempts", type=int, default=None, help="total provider request attempts; overrides speed-profile default")
    regression.add_argument("--retry-base-seconds", type=float, default=5.0)
    regression.add_argument("--qa-fail-policy", choices=("retry", "fail", "warn"), default="retry")
    regression.add_argument("--simplified-chinese-policy", choices=("normalize", "warn", "fail"), default=os.environ.get("NTPE_SIMPLIFIED_CHINESE_POLICY", "normalize"))
    regression.add_argument("--api-timeout", type=int, default=int(os.environ.get("NTPE_API_TIMEOUT", "180")), help="NVIDIA API read timeout in seconds; default 180 for literary regression")
    regression.add_argument("--api-connect-timeout", type=int, default=int(os.environ.get("NTPE_API_CONNECT_TIMEOUT", "10")), help="NVIDIA API connect timeout in seconds")
    regression.add_argument("--no-progress", action="store_true", help="disable live NTPE progress messages")

    evaluate = sub.add_parser("evaluate", help="evaluate literary regression outputs without rerunning translation")
    evaluate.add_argument("--stage", default=os.environ.get("NTPE_PS_STAGE", "PS-03"), help="stage output folder under tests/literary/outputs")
    evaluate.add_argument("--previous-stage", default=None, help="optional previous stage folder for diff report")

    corpus = sub.add_parser("corpus", help="inspect or initialize literary regression corpus")
    corpus.add_argument("action", choices=("init", "list"), nargs="?", default="list")

    doctor = sub.add_parser("doctor", help="check production translator environment")
    doctor.add_argument("--strict", action="store_true", help="fail when NVIDIA_API_KEY is missing")
    return parser


def _print_regression_result(report: dict) -> int:
    print("NTPE Literary Regression")
    print("========================")
    print(f"status: {report.get('status')}")
    print(f"stage: {report.get('stage')}")
    print(f"profile: {report.get('profile')}")
    print(f"output_dir: {report.get('output_dir')}")
    summary = report.get("summary", {})
    print(f"sets: {summary.get('success', 0)} success / {summary.get('skipped', 0)} skipped / {summary.get('failed', 0)} failed / {summary.get('total', 0)} total")
    print(f"dry_run: {summary.get('dry_run')}")
    return 0 if report.get("status") == "success" else 1




def _apply_runtime_timeout_env(args: argparse.Namespace) -> None:
    """Apply CLI timeout overrides before Translation Runtime calls providers.

    Regression/golden tests are often longer than smoke tests, so the CLI must
    propagate timeout settings explicitly instead of silently falling back to the
    provider transport default.
    """
    api_timeout = getattr(args, "api_timeout", None)
    api_connect_timeout = getattr(args, "api_connect_timeout", None)
    if api_timeout is not None:
        os.environ["NTPE_API_TIMEOUT"] = str(max(1, int(api_timeout)))
        os.environ["NTPE_API_TIMEOUT_EXPLICIT"] = "1"
    if api_connect_timeout is not None:
        os.environ["NTPE_API_CONNECT_TIMEOUT"] = str(max(1, int(api_connect_timeout)))



def _apply_provider_env(args: argparse.Namespace) -> None:
    fallback_models = getattr(args, "fallback_models", None)
    if fallback_models is not None:
        os.environ["NTPE_FALLBACK_MODELS"] = str(fallback_models).strip()

def _normalize_regression_sets(values: list[str] | None) -> tuple[str, ...]:
    if not values:
        return ("Smoke_Set", "Golden_Set", "Regression_Set")
    aliases = {
        "smoke": "Smoke_Set",
        "Smoke_Set": "Smoke_Set",
        "Test_Set_0": "Smoke_Set",
        "golden": "Golden_Set",
        "Golden_Set": "Golden_Set",
        "Test_Set_A": "Golden_Set",
        "regression": "Regression_Set",
        "Regression_Set": "Regression_Set",
        "Test_Set_B": "Regression_Set",
    }
    normalized: list[str] = []
    for value in values:
        mapped = aliases.get(value)
        if not mapped:
            raise ValueError(f"Unknown regression set: {value}")
        if mapped not in normalized:
            normalized.append(mapped)
    return tuple(normalized)

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
    checks.append(("NTPE_CHUNK_SIZE", True, os.environ.get("NTPE_CHUNK_SIZE", "1000")))
    checks.append(("NTPE_TRANSLATION_PROFILE", True, os.environ.get("NTPE_TRANSLATION_PROFILE", "literary")))
    checks.append(("NTPE_MAX_OUTPUT_TOKENS", True, os.environ.get("NTPE_MAX_OUTPUT_TOKENS", "auto")))
    checks.append(("NTPE_FALLBACK_MODELS", True, os.environ.get("NTPE_FALLBACK_MODELS", "not configured")))
    checks.append(("literary_corpus", (ROOT / "tests" / "literary").exists(), "tests/literary"))
    failed = False
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        print(f"{name:<24} {status:<5} {detail}")
        failed = failed or not ok
    return 1 if failed else 0


def run_txt(args: argparse.Namespace) -> int:
    _apply_runtime_timeout_env(args)
    _apply_provider_env(args)
    runtime = TranslationRuntime(root=ROOT)
    options = TxtTranslationOptions(
        input_path=_resolve(args.input),
        output_dir=_resolve(args.output),
        chunk_size=max(300, args.chunk_size) if args.chunk_size is not None else 1000,
        chunk_size_explicit=args.chunk_size is not None,
        model=args.model,
        resume=not args.no_resume,
        dry_run=args.dry_run,
        max_retries=max(0, args.max_retries),
        provider_attempts=max(1, args.provider_attempts) if args.provider_attempts is not None else None,
        retry_base_seconds=max(0.0, args.retry_base_seconds),
        glossary_path=Path(args.glossary) if args.glossary else None,
        character_memory_path=Path(args.character_memory) if args.character_memory else None,
        qa_enabled=not args.no_qa,
        qa_fail_policy=args.qa_fail_policy,
        min_length_ratio=max(0.0, args.min_length_ratio),
        max_korean_chars=max(0, args.max_korean_chars),
        max_repeated_lines=max(0, args.max_repeated_lines),
        quality_profile=args.profile,
        simplified_chinese_policy=args.simplified_chinese_policy,
        progress_enabled=not getattr(args, "no_progress", False),
        speed=args.speed,
    )
    return _print_result("NTPE Production TXT Translation", runtime.translate_txt(options))


def run_batch(args: argparse.Namespace) -> int:
    _apply_runtime_timeout_env(args)
    _apply_provider_env(args)
    runtime = TranslationRuntime(root=ROOT)
    options = BatchTranslationOptions(
        input_dir=_resolve(args.input),
        output_dir=_resolve(args.output),
        recursive=args.recursive,
        chunk_size=max(300, args.chunk_size) if args.chunk_size is not None else 1000,
        chunk_size_explicit=args.chunk_size is not None,
        model=args.model,
        resume=not args.no_resume,
        dry_run=args.dry_run,
        max_retries=max(0, args.max_retries),
        provider_attempts=max(1, args.provider_attempts) if args.provider_attempts is not None else None,
        retry_base_seconds=max(0.0, args.retry_base_seconds),
        glossary_path=Path(args.glossary) if args.glossary else None,
        character_memory_path=Path(args.character_memory) if args.character_memory else None,
        qa_enabled=not args.no_qa,
        qa_fail_policy=args.qa_fail_policy,
        min_length_ratio=max(0.0, args.min_length_ratio),
        max_korean_chars=max(0, args.max_korean_chars),
        max_repeated_lines=max(0, args.max_repeated_lines),
        quality_profile=args.profile,
        speed=args.speed,
        simplified_chinese_policy=args.simplified_chinese_policy,
        continue_on_failure=args.continue_on_failure,
        auto_recovery=args.auto_recovery,
        heartbeat=args.heartbeat,
        progress_enabled=not getattr(args, "no_progress", False),
    )
    return _print_result("NTPE Production Batch Translation", runtime.translate_batch(options))


def run_corpus(args: argparse.Namespace) -> int:
    if args.action == "init":
        result = ensure_literary_structure(ROOT)
        print("NTPE Literary Corpus Init")
        print("=========================")
        print(f"status: {result.get('status')}")
        print(f"literary_root: {result.get('literary_root')}")
        for item in result.get("created", []):
            print(f"created: {item}")
        return 0
    print("NTPE Literary Corpus")
    print("====================")
    for item in discover_test_sets(ROOT):
        status = "READY" if item.get("exists") and item.get("has_content") else "EMPTY" if item.get("exists") else "MISSING"
        print(f"{item.get('name'):<12} {status:<7} {item.get('source')}")
    return 0


def run_evaluate(args: argparse.Namespace) -> int:
    report = evaluate_stage_outputs(ROOT, args.stage, previous_stage=args.previous_stage)
    print("NTPE Literary Evaluation")
    print("========================")
    print(f"status: {report.get('status')}")
    print(f"stage: {report.get('stage')}")
    print(f"overall_score: {report.get('summary', {}).get('overall_score', 0)}")
    print(f"report_md: {report.get('report_md')}")
    print(f"report_json: {report.get('report_json')}")
    return 0 if report.get("status") in ("success", "warning") else 1


def run_regression(args: argparse.Namespace) -> int:
    _apply_runtime_timeout_env(args)
    _apply_provider_env(args)
    options = LiteraryRegressionOptions(
        root=ROOT,
        test_sets=_normalize_regression_sets(args.sets),
        stage_name=args.stage,
        profile=args.profile,
        chunk_size=max(300, args.chunk_size) if args.chunk_size is not None else 1000,
        chunk_size_explicit=args.chunk_size is not None,
        speed=args.speed,
        model=args.model,
        dry_run=args.dry_run,
        overwrite=args.overwrite,
            resume=not args.no_resume,
        max_retries=max(0, args.max_retries),
        provider_attempts=max(1, args.provider_attempts) if args.provider_attempts is not None else None,
        retry_base_seconds=max(0.0, args.retry_base_seconds),
        qa_fail_policy=args.qa_fail_policy,
        simplified_chinese_policy=args.simplified_chinese_policy,
        evaluate=not args.no_evaluate,
        previous_stage=args.previous_stage,
        progress_enabled=not getattr(args, "no_progress", False),
    )
    return _print_regression_result(run_literary_regression(options))


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
    if args.command == "corpus":
        return run_corpus(args)
    if args.command == "regression":
        return run_regression(args)
    if args.command == "evaluate":
        return run_evaluate(args)
    if args.command == "txt":
        return run_txt(args)
    if args.command == "batch":
        return run_batch(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
