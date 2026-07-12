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
from core.adaptive_context_runtime_shadow import install_txt_runtime_shadow_hook
from core.adaptive_context_production_validation import (
    build_production_shadow_report,
    production_shadow_session,
    write_production_shadow_report,
)
from core.adaptive_context_canary_resume import prepare_canary_resume
from core.adaptive_context_canary_ab import evaluate_canary_ab, load_stage_evidence, write_ab_report
from core.adaptive_context_activation_policy import (
    ActivationPolicyRequest,
    evaluate_activation_policy,
    load_activation_evidence,
    write_activation_policy_report,
)
from core.adaptive_context_canary_validation import (
    build_canary_production_report,
    canary_validation_session,
    write_canary_production_report,
)

# TE v7 Stage 03: installs a no-op-unless-shadow wrapper around prompt package
# construction. The wrapper returns the original package unchanged.
install_txt_runtime_shadow_hook()

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
    regression.add_argument("--ace-shadow-validate", action="store_true", help="run TE v7 ACE production shadow validation without changing prompt payload")
    regression.add_argument("--ace-shadow-report", default=None, help="optional JSON report path for ACE production shadow validation")
    regression.add_argument("--ace-canary-validate", action="store_true", help="run TE v7 single-chunk ACE production canary validation")
    regression.add_argument("--ace-canary-report", default=None, help="optional JSON report path for ACE production canary validation")
    regression.add_argument("--ace-canary-chunk", type=int, default=2, help="single chunk eligible for ACE canary activation")
    regression.add_argument("--ace-canary-context-tokens", type=int, default=128, help="context token budget for the ACE canary candidate")
    regression.add_argument("--ace-canary-resume-from-stage", default=None, help="seed completed chunks before the canary target from an earlier regression stage")
    regression.add_argument("--ace-canary-ab-validate", action="store_true", help="compare completed baseline and canary quality evidence without calling Provider")
    regression.add_argument("--ace-canary-ab-baseline-stage", default=None, help="baseline regression stage for A/B quality validation")
    regression.add_argument("--ace-canary-ab-canary-stage", default=None, help="canary regression stage for A/B quality validation")
    regression.add_argument("--ace-canary-ab-report", default=None, help="optional A/B quality validation JSON path")
    regression.add_argument("--ace-production-policy-validate", action="store_true", help="evaluate TE v7 ACE production activation policy without calling Provider")
    regression.add_argument("--ace-production-policy-ab-report", default=None, help="A/B quality report used by the production activation policy")
    regression.add_argument("--ace-production-policy-canary-report", default=None, help="canary production report used by the activation policy")
    regression.add_argument("--ace-production-policy-report", default=None, help="optional production activation policy decision JSON path")
    regression.add_argument("--ace-production-rollout-percent", type=int, default=0, help="requested Stage 08.1 rollout percent; maximum 5")
    regression.add_argument("--ace-production-enable", action="store_true", help="explicitly request production-canary eligibility evaluation")
    regression.add_argument("--ace-production-kill-switch", action="store_true", help="force the production activation policy to fail closed")

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
    if bool(getattr(args, "ace_production_policy_validate", False)):
        ab_path = _resolve(args.ace_production_policy_ab_report) if args.ace_production_policy_ab_report else ROOT / "artifacts" / "te_v7_stage075" / "TE_V7_STAGE075_CANARY_AB_QUALITY_VALIDATION.json"
        canary_path = _resolve(args.ace_production_policy_canary_report) if args.ace_production_policy_canary_report else ROOT / "artifacts" / "te_v7_stage06" / "TE_V7_STAGE06_CANARY_PRODUCTION_VALIDATION.json"
        out_path = _resolve(args.ace_production_policy_report) if args.ace_production_policy_report else ROOT / "artifacts" / "te_v7_stage081" / "TE_V7_STAGE081_PRODUCTION_ACTIVATION_POLICY.json"
        try:
            evidence = load_activation_evidence(ab_path, canary_path)
            decision = evaluate_activation_policy(
                evidence,
                ActivationPolicyRequest(
                    profile=args.profile,
                    rollout_percent=max(0, int(args.ace_production_rollout_percent)),
                    explicitly_enabled=bool(args.ace_production_enable),
                    kill_switch=bool(args.ace_production_kill_switch),
                ),
            )
        except (OSError, ValueError, TypeError) as exc:
            print(f"ACE production policy validation error: {exc}")
            return 2
        write_activation_policy_report(decision, out_path)
        print(f"ace_production_policy_report: {out_path}")
        print(f"ace_production_policy_status: {decision.status}")
        print(f"ace_production_policy_ready: {str(decision.ready).lower()}")
        print(f"ace_production_policy_mode: {decision.mode}")
        print(f"ace_production_policy_rollout_percent: {decision.rollout_percent}")
        print(f"ace_production_policy_blockers: {','.join(decision.blockers) or 'none'}")
        return 0 if decision.ready else 1
    if bool(getattr(args, "ace_canary_ab_validate", False)):
        baseline_stage=str(getattr(args,"ace_canary_ab_baseline_stage","") or "").strip()
        canary_stage=str(getattr(args,"ace_canary_ab_canary_stage","") or "").strip()
        if not baseline_stage or not canary_stage:
            print("ACE A/B validation error: baseline and canary stages are required")
            return 2
        chunk=max(1,int(getattr(args,"ace_canary_chunk",2)))
        try:
            baseline=load_stage_evidence(ROOT,baseline_stage,chunk)
            canary=load_stage_evidence(ROOT,canary_stage,chunk)
            report=evaluate_canary_ab(baseline,canary)
        except (OSError,ValueError,TypeError) as exc:
            print(f"ACE A/B validation error: {exc}")
            return 2
        path=_resolve(args.ace_canary_ab_report) if args.ace_canary_ab_report else ROOT/"artifacts"/"te_v7_stage075"/"TE_V7_STAGE075_CANARY_AB_QUALITY_VALIDATION.json"
        write_ab_report(report,path)
        print(f"ace_canary_ab_report: {path}")
        print(f"ace_canary_ab_status: {report.status}")
        print(f"ace_canary_ab_ready: {str(report.ready).lower()}")
        print(f"ace_canary_ab_blockers: {','.join(report.blockers) or 'none'}")
        return 0 if report.ready else 1
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
    shadow_validate = bool(getattr(args, "ace_shadow_validate", False))
    canary_validate = bool(getattr(args, "ace_canary_validate", False))
    if shadow_validate and canary_validate:
        print("ACE validation error: --ace-shadow-validate and --ace-canary-validate are mutually exclusive")
        return 2
    if not shadow_validate and not canary_validate:
        return _print_regression_result(run_literary_regression(options))

    if canary_validate:
        report_path = _resolve(args.ace_canary_report) if args.ace_canary_report else (
            ROOT / "artifacts" / "te_v7_stage06" / "TE_V7_STAGE06_CANARY_PRODUCTION_VALIDATION.json"
        )
        target_chunk = max(1, int(args.ace_canary_chunk))
        context_tokens = max(1, int(args.ace_canary_context_tokens))
        audit_path = str(report_path.with_suffix(".jsonl"))
        if getattr(args, "ace_canary_resume_from_stage", None):
            if args.overwrite:
                options = LiteraryRegressionOptions(**{**options.__dict__, "overwrite": False})
            resume_plan = prepare_canary_resume(
                ROOT, source_stage=args.ace_canary_resume_from_stage, target_stage=args.stage, target_chunk=target_chunk
            )
            print(f"ace_canary_resume_ready: {str(resume_plan.ready).lower()}")
            print(f"ace_canary_resume_copied: {len(resume_plan.copied_chunks)}")
            if not resume_plan.ready:
                print(f"ace_canary_resume_missing: {','.join(map(str, resume_plan.missing_chunks))}")
                return 2
        with canary_validation_session(
            target_chunk=target_chunk,
            context_tokens=context_tokens,
            audit_path=audit_path,
        ):
            regression_result = run_literary_regression(options)
        report = build_canary_production_report(
            regression_result,
            target_chunk=target_chunk,
            provider_execution_requested=not args.dry_run,
            stage=args.stage,
        )
        write_canary_production_report(report, report_path)
        print(f"ace_canary_report: {report_path}")
        print(f"ace_canary_status: {report.status}")
        print(f"ace_canary_records: {report.records}")
        print(f"ace_canary_activated: {report.activated_records}")
        print(f"ace_canary_tokens_saved: {report.estimated_tokens_saved}")
        print(f"ace_canary_fallback_reasons: {','.join(report.fallback_reasons) or 'none'}")
        print(f"ace_canary_target_complete: {str(report.target_chunk_completed).lower()}")
        print(f"ace_canary_latency_average_ms: {report.canary_latency_average_ms}")
        display_result = regression_result
        if report.target_chunk_completed and not report.blockers:
            display_result = dict(regression_result)
            display_result["status"] = "target_complete"
            summary = dict(regression_result.get("summary", {}))
            summary["failed"] = 0
            summary["success"] = max(1, int(summary.get("success", 0) or 0))
            display_result["summary"] = summary
        base_rc = _print_regression_result(display_result)
        canary_gate_passed = report.ready or (bool(args.dry_run) and not report.blockers)
        if report.target_chunk_completed and not report.blockers:
            base_rc = 0
        return 0 if base_rc == 0 and canary_gate_passed else 1

    report_path = _resolve(args.ace_shadow_report) if args.ace_shadow_report else (
        ROOT / "artifacts" / "te_v7_stage04" / "TE_V7_STAGE04_PRODUCTION_SHADOW_VALIDATION.json"
    )
    audit_path = str(report_path.with_suffix(".jsonl"))
    with production_shadow_session(audit_path=audit_path):
        regression_result = run_literary_regression(options)
    report = build_production_shadow_report(
        regression_result,
        provider_execution_requested=not args.dry_run,
        stage=args.stage,
    )
    write_production_shadow_report(report, report_path)
    print(f"ace_shadow_report: {report_path}")
    print(f"ace_shadow_status: {report.status}")
    print(f"ace_shadow_records: {report.shadow_records}")
    print(f"ace_payload_equivalent: {report.payload_equivalent_records}/{report.shadow_records}")
    print(f"ace_latency_average_ms: {report.ace_latency_average_ms}")
    base_rc = _print_regression_result(regression_result)
    return 0 if base_rc == 0 and report.ready else 1


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
