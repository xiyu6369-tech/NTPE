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

from core.production_runtime.manifest import (
    get_te_v7_artifact_path,
    get_te_v7_stage_path,
    TE_V7_STAGE09_BASELINE,
    TE_V7_STAGE09_CANDIDATE,
    TE_V7_STAGE09_COMPARISON,
    TE_V7_STAGE09_READINESS,
    TE_V7_STAGE081_PRODUCTION_ACTIVATION_POLICY,
    TE_V7_STAGE082_PROFILE_AWARE_CONTEXT_BUDGET,
    TE_V7_STAGE083_ADAPTIVE_CONTEXT_STRATEGY_SELECTION,
    TE_V7_STAGE075_CANARY_AB_QUALITY_VALIDATION,
    TE_V7_STAGE06_CANARY_PRODUCTION_VALIDATION,
    TE_V7_STAGE04_PRODUCTION_SHADOW_VALIDATION,
)
from ntpe_literary_regression import LiteraryRegressionOptions, discover_test_sets, ensure_literary_structure, run_literary_regression
from ntpe_literary_evaluation import evaluate_stage_outputs
from core.adapters.epub_extraction_boundary import (
    EpubExtractionBoundary,
    EpubExtractionError,
    EpubExtractionResult,
    ExtractedTextIntakeRequest,
)
from core.adapters.canonical_book_intake_adapter import CanonicalBookIntakeAdapter, CanonicalIntakeResult

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
from core.adaptive_context_profile_budget import (
    ProfileBudgetRequest,
    evaluate_profile_budget,
    write_profile_budget_report,
)
from core.adaptive_context_strategy_selection import (
    StrategySelectionRequest,
    evaluate_strategy_selection,
    load_strategy_selection_evidence,
    write_strategy_selection_report,
)
from core.adaptive_context_canary_validation import (
    build_canary_production_report,
    canary_validation_session,
    write_canary_production_report,
)
from core.adaptive_context_production_rollout import (
    RollbackController,
    RolloutConfig,
    RolloutMetrics,
    collect_production_outcome,
    evaluate_automatic_rollback,
    install_production_rollout_hook,
    load_production_evidence,
    prior_rollback_reasons,
    production_rollout_session,
    rollback_quality_inputs,
    snapshot_resume_chunks,
    write_metrics_report,
)
from core.adaptive_context_production_rollout.model import RollbackDecision
from core.adaptive_context_production_benchmark import (
    BenchmarkConfig,
    collect_regression_run,
    compare_runs,
    load_run,
    write_artifact,
)

# TE v7 Stage 03: installs a no-op-unless-shadow wrapper around prompt package
# construction. The wrapper returns the original package unchanged.
install_txt_runtime_shadow_hook()
install_production_rollout_hook()

DEFAULT_MODEL = "meta/llama-3.2-90b-vision-instruct"


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
    txt.add_argument("--pipeline", choices=("runtime", "legacy"), default=os.environ.get("NTPE_RUNTIME_PIPELINE", "runtime"), help="translation pipeline mode; default: runtime (env: NTPE_RUNTIME_PIPELINE)")
    txt.add_argument("--quality-delivery-v83", action="store_true", help="enable RM-8.3 delivery pipeline")
    txt.add_argument("--quality-delivery-formats-v83", nargs="+", default=["txt"], choices=["txt", "epub", "pdf"], help="output formats for RM-8.3 delivery (default: txt)")
    _add_quality_integration_v72_flags(txt)

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
    batch.add_argument("--pipeline", choices=("runtime", "legacy"), default=os.environ.get("NTPE_RUNTIME_PIPELINE", "runtime"), help="translation pipeline mode; default: runtime (env: NTPE_RUNTIME_PIPELINE)")
    batch.add_argument("--quality-delivery-v83", action="store_true", help="enable RM-8.3 delivery pipeline")
    batch.add_argument("--quality-delivery-formats-v83", nargs="+", default=["txt"], choices=["txt", "epub", "pdf"], help="output formats for RM-8.3 delivery (default: txt)")
    _add_quality_integration_v72_flags(batch)

    epub = sub.add_parser("epub", help="translate an EPUB file")
    epub.add_argument("input", help="input EPUB file path")
    epub.add_argument("output", nargs="?", default="output", help="output directory")
    epub.add_argument("--chunk-size", type=int, default=None)
    epub.add_argument("--speed", choices=("fast", "balanced", "quality"), default=os.environ.get("NTPE_TRANSLATION_SPEED", "balanced"))
    epub.add_argument("--model", default=DEFAULT_MODEL)
    epub.add_argument("--fallback-models", default=os.environ.get("NTPE_FALLBACK_MODELS", ""), help="comma-separated fallback NVIDIA model IDs")
    epub.add_argument("--glossary", default=None)
    epub.add_argument("--character-memory", default=None)
    epub.add_argument("--max-retries", type=int, default=3)
    epub.add_argument("--provider-attempts", type=int, default=None, help="total provider request attempts; overrides speed-profile default")
    epub.add_argument("--retry-base-seconds", type=float, default=5.0)
    epub.add_argument("--qa-fail-policy", choices=("retry", "fail", "warn"), default="retry")
    epub.add_argument("--min-length-ratio", type=float, default=0.25)
    epub.add_argument("--max-korean-chars", type=int, default=3)
    epub.add_argument("--max-repeated-lines", type=int, default=2)
    epub.add_argument("--no-resume", action="store_true")
    epub.add_argument("--no-qa", action="store_true")
    epub.add_argument("--profile", choices=("fast", "balanced", "novel", "literary", "quality", "premium"), default=os.environ.get("NTPE_TRANSLATION_PROFILE", "literary"))
    epub.add_argument("--simplified-chinese-policy", choices=("normalize", "warn", "fail"), default=os.environ.get("NTPE_SIMPLIFIED_CHINESE_POLICY", "normalize"))
    epub.add_argument("--api-timeout", type=int, default=None, help="provider read timeout upper bound in seconds")
    epub.add_argument("--api-connect-timeout", type=int, default=None, help="provider connect timeout in seconds")
    epub.add_argument("--dry-run", action="store_true", help="build packages only; do not call NVIDIA API")
    epub.add_argument("--no-progress", action="store_true", help="disable live NTPE progress messages")
    epub.add_argument("--pipeline", choices=("runtime", "legacy"), default=os.environ.get("NTPE_RUNTIME_PIPELINE", "runtime"), help="translation pipeline mode; default: runtime (env: NTPE_RUNTIME_PIPELINE)")
    epub.add_argument("--quality-delivery-v83", action="store_true", help="enable RM-8.3 delivery pipeline")
    epub.add_argument("--quality-delivery-formats-v83", nargs="+", default=["txt"], choices=["txt", "epub", "pdf"], help="output formats for RM-8.3 delivery (default: txt)")
    _add_quality_integration_v72_flags(epub)

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
    regression.add_argument("--ace-profile-budget-validate", action="store_true", help="evaluate TE v7 profile-aware context budget without calling Provider")
    regression.add_argument("--ace-profile-budget-report", default=None, help="optional profile-aware context budget JSON path")
    regression.add_argument("--ace-profile-budget-model-limit", type=int, default=8192, help="model context limit used by the assembly-only budget validator")
    regression.add_argument("--ace-profile-budget-fixed-prompt-tokens", type=int, default=512, help="fixed prompt tokens reserved before context")
    regression.add_argument("--ace-profile-budget-source-tokens", type=int, default=1024, help="source tokens reserved before context")
    regression.add_argument("--ace-profile-budget-output-tokens", type=int, default=1024, help="output tokens reserved before context")
    regression.add_argument("--ace-profile-budget-requested-tokens", type=int, default=None, help="optional requested context tokens; clamped by profile and hard limit")
    regression.add_argument("--ace-strategy-select-validate", action="store_true", help="select a TE v7 ACE context strategy from policy and profile-budget evidence")
    regression.add_argument("--ace-strategy-policy-report", default=None, help="production activation policy report used for strategy selection")
    regression.add_argument("--ace-strategy-budget-report", default=None, help="profile-aware context budget report used for strategy selection")
    regression.add_argument("--ace-strategy-report", default=None, help="optional adaptive context strategy selection JSON path")
    regression.add_argument("--ace-strategy-enable", action="store_true", help="explicitly request adaptive context strategy selection")
    regression.add_argument("--ace-strategy-kill-switch", action="store_true", help="force strategy selection to fail closed")
    regression.add_argument("--ace-production-rollout", action="store_true", help="explicitly opt in to TE v7 Stage 08.4 production rollout")
    regression.add_argument("--ace-production-budget-report", default=None, help="Stage 08.2 budget evidence for production rollout")
    regression.add_argument("--ace-production-strategy-report", default=None, help="Stage 08.3 strategy evidence for production rollout")
    regression.add_argument("--ace-production-metrics-report", default=None, help="redacted Stage 08.4 rollout metrics JSON path")
    regression.add_argument("--ace-production-rollback-report", default=None, help="redacted Stage 08.4 rollback decision JSON path")
    regression.add_argument("--ace-production-validation-mode", choices=("assembly-only", "shadow-compatible", "provider"), default=None)
    regression.add_argument("--ace-production-resume-from-stage", default=None, help="resume completed chunks before the production validation target")
    regression.add_argument("--ace-production-target-chunk", type=int, default=None, help="stop production validation after this chunk")
    regression.add_argument("--ace-production-simulate-rollback", action="store_true", help="simulate fail-closed automatic rollback")
    regression.add_argument("--ace-production-benchmark", action="store_true", help="run the redacted TE v7 Stage 09 production benchmark")
    regression.add_argument("--ace-production-benchmark-mode", choices=("assembly", "provider", "comparison"), default="assembly")
    regression.add_argument("--ace-production-benchmark-report", default=None, help="optional Stage 09 baseline, candidate, or comparison JSON path")
    regression.add_argument("--ace-production-benchmark-baseline-stage", default=None, help="completed Stage 09 baseline artifact or stage name")
    regression.add_argument("--ace-production-benchmark-candidate-stage", default=None, help="completed Stage 09 candidate artifact or stage name")
    regression.add_argument("--ace-production-benchmark-target-chunk", type=int, default=None)
    regression.add_argument("--ace-production-benchmark-resume-from-stage", default=None)

    evaluate = sub.add_parser("evaluate", help="evaluate literary regression outputs without rerunning translation")
    evaluate.add_argument("--stage", default=os.environ.get("NTPE_PS_STAGE", "PS-03"), help="stage output folder under tests/literary/outputs")
    evaluate.add_argument("--previous-stage", default=None, help="optional previous stage folder for diff report")

    corpus = sub.add_parser("corpus", help="inspect or initialize literary regression corpus")
    corpus.add_argument("action", choices=("init", "list"), nargs="?", default="list")

    doctor = sub.add_parser("doctor", help="check production translator environment")
    doctor.add_argument("--strict", action="store_true", help="fail when NVIDIA_API_KEY is missing")
    return parser


def _add_quality_integration_v72_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--quality-integration-v72", action="store_true", help="enable all TE v7.2 Milestone A prompt integrations")
    parser.add_argument("--quality-character-memory-v72", action="store_true", help="enable eligible Character Memory prompt integration")
    parser.add_argument("--quality-context-scene-v72", action="store_true", help="enable eligible Context/Scene Memory prompt integration")
    parser.add_argument("--quality-naturalness-v72", action="store_true", help="enable the fidelity-first naturalness policy")
    parser.add_argument("--quality-integration-kill-switch-v72", action="store_true", help="disable all TE v7.2 quality integration immediately")


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
    pipeline_mode = getattr(args, "pipeline", None) or os.environ.get("NTPE_RUNTIME_PIPELINE", "runtime")
    os.environ["NTPE_RUNTIME_PIPELINE"] = pipeline_mode
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
        quality_integration_v72=args.quality_integration_v72,
        quality_character_memory_v72=args.quality_character_memory_v72,
        quality_context_scene_v72=args.quality_context_scene_v72,
        quality_naturalness_v72=args.quality_naturalness_v72,
        quality_integration_kill_switch_v72=args.quality_integration_kill_switch_v72,
        quality_delivery_v83=args.quality_delivery_v83,
        quality_delivery_formats_v83=tuple(args.quality_delivery_formats_v83) if args.quality_delivery_formats_v83 else ("txt",),
    )
    return _print_result("NTPE Production TXT Translation", runtime.translate_txt(options))


def run_batch(args: argparse.Namespace) -> int:
    _apply_runtime_timeout_env(args)
    _apply_provider_env(args)
    pipeline_mode = getattr(args, "pipeline", None) or os.environ.get("NTPE_RUNTIME_PIPELINE", "runtime")
    os.environ["NTPE_RUNTIME_PIPELINE"] = pipeline_mode
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
        quality_integration_v72=args.quality_integration_v72,
        quality_character_memory_v72=args.quality_character_memory_v72,
        quality_context_scene_v72=args.quality_context_scene_v72,
        quality_naturalness_v72=args.quality_naturalness_v72,
        quality_integration_kill_switch_v72=args.quality_integration_kill_switch_v72,
        quality_delivery_v83=args.quality_delivery_v83,
        quality_delivery_formats_v83=tuple(args.quality_delivery_formats_v83) if args.quality_delivery_formats_v83 else ("txt",),
    )
    return _print_result("NTPE Production Batch Translation", runtime.translate_batch(options))


def run_epub(args: argparse.Namespace) -> int:
    _apply_runtime_timeout_env(args)
    _apply_provider_env(args)
    pipeline_mode = getattr(args, "pipeline", None) or os.environ.get("NTPE_RUNTIME_PIPELINE", "runtime")
    os.environ["NTPE_RUNTIME_PIPELINE"] = pipeline_mode

    # Step 1: Extract EPUB
    epub_path = _resolve(args.input)
    if not epub_path.exists():
        print(f"EPUB file not found: {epub_path}")
        return 1
    if epub_path.suffix.lower() != ".epub":
        print(f"Input file is not an EPUB: {epub_path}")
        return 1

    print(f"NTPE Production EPUB Translation")
    print(f"==================================")
    print(f"Input: {epub_path}")
    print(f"Output: {_resolve(args.output)}")

    extractor = EpubExtractionBoundary()
    try:
        extraction_result: EpubExtractionResult = extractor.extract(epub_path)
    except EpubExtractionError as e:
        print(f"EPUB extraction failed: {e}")
        if e.blocked:
            return 1
        # For manual_review_required, we could still proceed but warn
        print(f"Warning: {e}")

    # Step 2: Create intake request from extraction result
    intake_request = ExtractedTextIntakeRequest(
        source_path=extraction_result.source_path,
        source_format="epub",
        extracted_text=extraction_result.extracted_text,
        original_file_hash=extraction_result.original_hash,
        extracted_text_hash=extraction_result.extracted_hash,
        epub_metadata=dict(extraction_result.metadata.raw) if extraction_result.metadata.raw else {},
        chapter_map=extraction_result.chapter_map,
        extraction_manifest=extraction_result.extraction_manifest,
        extractor_version=extraction_result.extractor_version,
        status=extraction_result.status,
        warnings=extraction_result.warnings,
    )

    # Step 3: Process through canonical intake adapter
    adapter = CanonicalBookIntakeAdapter()
    try:
        intake_result: CanonicalIntakeResult = adapter.ingest_extracted(intake_request)
    except EpubExtractionError as e:
        print(f"EPUB intake failed: {e}")
        return 1

    if not intake_result.submission_eligible:
        print(f"EPUB intake not eligible for translation: {intake_result.status}")
        for w in intake_result.warnings:
            print(f"  Warning: {w}")
        return 1

    # Step 4: Write extracted text to a temporary file and use existing TXT pipeline
    # This reuses the entire TXT translation pipeline (chunker, runtime, QA, etc.)
    from lts.txt_translation_runtime import TxtTranslationOptions
    import tempfile

    output_dir = _resolve(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create temporary TXT file with extracted text
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
        tmp.write(extraction_result.extracted_text)
        tmp_path = Path(tmp.name)

    try:
        # Build options for TXT translation
        options = TxtTranslationOptions(
            input_path=tmp_path,
            output_dir=output_dir,
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
            quality_integration_v72=args.quality_integration_v72,
            quality_character_memory_v72=args.quality_character_memory_v72,
            quality_context_scene_v72=args.quality_context_scene_v72,
            quality_naturalness_v72=args.quality_naturalness_v72,
            quality_integration_kill_switch_v72=args.quality_integration_kill_switch_v72,
            quality_delivery_v83=args.quality_delivery_v83,
            quality_delivery_formats_v83=tuple(args.quality_delivery_formats_v83) if args.quality_delivery_formats_v83 else ("txt",),
        )

        # Use existing TXT translation runtime
        runtime = TranslationRuntime(root=ROOT)
        result = runtime.translate_txt(options)

        # Rename output file to use EPUB stem instead of temp file stem
        if result.get("status") == "success":
            original_output = Path(result.get("output", ""))
            if original_output.exists():
                # The output file is named after the temp file, rename it
                new_output = output_dir / f"{epub_path.stem}{DEFAULT_OUTPUT_SUFFIX}.txt"
                if original_output != new_output:
                    import shutil
                    shutil.move(str(original_output), str(new_output))
                    result["output"] = str(new_output)

        # Add EPUB-specific metadata to result
        result["epub_metadata"] = intake_result.epub_metadata
        result["chapter_map"] = [c.__dict__ for c in intake_result.chapter_map] if intake_result.chapter_map else None
        result["extraction_status"] = extraction_result.status
        result["extraction_warnings"] = extraction_result.warnings

        return _print_result("NTPE Production EPUB Translation", result)

    finally:
        # Clean up temp file
        try:
            tmp_path.unlink()
        except Exception:
            pass


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


def _stage09_artifact(kind: str) -> Path:
    artifact_map = {
        "baseline": TE_V7_STAGE09_BASELINE,
        "candidate": TE_V7_STAGE09_CANDIDATE,
        "comparison": TE_V7_STAGE09_COMPARISON,
        "readiness": TE_V7_STAGE09_READINESS,
    }
    artifact_name = artifact_map.get(kind.lower())
    if artifact_name is None:
        raise ValueError(f"Unknown stage09 artifact kind: {kind}")
    return get_te_v7_artifact_path(ROOT, "te_v7_stage09", artifact_name)


def _benchmark_input(value: str, kind: str) -> tuple[Path, str | None]:
    candidate = _resolve(value)
    if candidate.is_file():
        return candidate, None
    return _stage09_artifact(kind), value


def _run_production_benchmark_comparison(args: argparse.Namespace) -> int:
    baseline_path, expected_baseline = _benchmark_input(str(args.ace_production_benchmark_baseline_stage), "baseline")
    candidate_path, expected_candidate = _benchmark_input(str(args.ace_production_benchmark_candidate_stage), "candidate")
    try:
        baseline = load_run(baseline_path)
        candidate = load_run(candidate_path)
        if expected_baseline and baseline.stage != expected_baseline:
            raise ValueError("baseline stage artifact mismatch")
        if expected_candidate and candidate.stage != expected_candidate:
            raise ValueError("candidate stage artifact mismatch")
        comparison = compare_runs(baseline, candidate)
    except (OSError, ValueError, TypeError) as exc:
        print(f"ACE production benchmark comparison error: {exc}")
        return 2
    report_path = _resolve(args.ace_production_benchmark_report) if args.ace_production_benchmark_report else _stage09_artifact("comparison")
    readiness_path = _stage09_artifact("readiness")
    write_artifact(comparison, report_path)
    write_artifact({
        "version": "7.0.0-stage09", "status": comparison.status, "ready": comparison.ready,
        "blockers": list(comparison.blockers), "limitations": list(comparison.limitations),
        "content_redacted": True,
    }, readiness_path)
    print(f"ace_production_benchmark_report: {report_path}")
    print(f"ace_production_benchmark_readiness: {readiness_path}")
    print(f"ace_production_benchmark_status: {comparison.status}")
    print(f"ace_production_benchmark_ready: {str(comparison.ready).lower()}")
    return 0 if comparison.ready else 1


def _write_production_benchmark_run(
    args: argparse.Namespace,
    regression_result: dict,
    mode: str,
    rollout_records: Iterable[dict],
    resume_snapshot: frozenset[tuple[str, int]],
    *,
    rollback_triggered: bool = False,
) -> Path:
    from core.translation_runtime.runtime_speed_policy import get_runtime_speed_policy

    candidate = bool(getattr(args, "ace_production_rollout", False))
    kind = "candidate" if candidate else "baseline"
    speed_policy = get_runtime_speed_policy(args.speed)
    run = collect_regression_run(
        root=ROOT, regression_result=regression_result, run_kind=kind, mode=mode,
        profile=args.profile, model=args.model, api_timeout=int(args.api_timeout or 0),
        provider_attempts=max(1, int(args.provider_attempts or speed_policy.provider_attempts)),
        chunk_size=max(300, int(args.chunk_size)) if args.chunk_size is not None else speed_policy.chunk_size,
        max_output_tokens=4096, ace_enabled=candidate,
        rollout_percent=int(args.ace_production_rollout_percent or 0) if candidate else 0,
        rollout_records=rollout_records, resume_snapshot=resume_snapshot,
        rollback_triggered=rollback_triggered,
    )
    path = _resolve(args.ace_production_benchmark_report) if args.ace_production_benchmark_report else _stage09_artifact(kind)
    write_artifact(run, path)
    print(f"ace_production_benchmark_report: {path}")
    print(f"ace_production_benchmark_kind: {kind}")
    print(f"ace_production_benchmark_provider_evidence_complete: {str(run.provider_evidence_complete).lower()}")
    return path


def run_regression(args: argparse.Namespace) -> int:
    benchmark_enabled = bool(getattr(args, "ace_production_benchmark", False))
    benchmark_mode = str(getattr(args, "ace_production_benchmark_mode", "assembly"))
    if benchmark_enabled:
        config = BenchmarkConfig(
            benchmark_mode, getattr(args, "ace_production_benchmark_report", None),
            getattr(args, "ace_production_benchmark_baseline_stage", None),
            getattr(args, "ace_production_benchmark_candidate_stage", None),
            getattr(args, "ace_production_benchmark_target_chunk", None),
            getattr(args, "ace_production_benchmark_resume_from_stage", None),
        )
        blockers = config.validate()
        if blockers:
            print(f"ACE production benchmark error: {','.join(blockers)}")
            return 2
        if benchmark_mode == "comparison":
            return _run_production_benchmark_comparison(args)
        if benchmark_mode == "assembly" and not args.dry_run:
            print("ACE production benchmark error: assembly mode requires --dry-run")
            return 2
        if benchmark_mode == "provider" and args.dry_run:
            print("ACE production benchmark error: provider mode cannot use --dry-run")
            return 2
        if getattr(args, "ace_production_benchmark_target_chunk", None) and not getattr(args, "ace_production_target_chunk", None):
            args.ace_production_target_chunk = args.ace_production_benchmark_target_chunk
        if getattr(args, "ace_production_benchmark_resume_from_stage", None) and not getattr(args, "ace_production_resume_from_stage", None):
            args.ace_production_resume_from_stage = args.ace_production_benchmark_resume_from_stage
    if bool(getattr(args, "ace_production_rollout", False)):
        conflicting = (
            bool(getattr(args, "ace_strategy_select_validate", False)),
            bool(getattr(args, "ace_profile_budget_validate", False)),
            bool(getattr(args, "ace_production_policy_validate", False)),
            bool(getattr(args, "ace_canary_validate", False)),
            bool(getattr(args, "ace_shadow_validate", False)),
        )
        if any(conflicting):
            print("ACE production rollout error: rollout and earlier-stage validation modes are mutually exclusive")
            return 2
        required = {
            "policy": getattr(args, "ace_production_policy_report", None),
            "budget": getattr(args, "ace_production_budget_report", None),
            "strategy": getattr(args, "ace_production_strategy_report", None),
            "metrics": getattr(args, "ace_production_metrics_report", None),
            "rollback": getattr(args, "ace_production_rollback_report", None),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            print(f"ACE production rollout error: missing required reports: {','.join(missing)}")
            return 2
        percent = int(getattr(args, "ace_production_rollout_percent", 0) or 0)
        if percent < 1 or percent > 5:
            print("ACE production rollout error: rollout percent must be from 1 through 5")
            return 2
        try:
            evidence = load_production_evidence(
                _resolve(required["policy"]), _resolve(required["budget"]), _resolve(required["strategy"])
            )
        except (OSError, ValueError, TypeError) as exc:
            print(f"ACE production rollout evidence error: {exc}")
            return 2
        mode = getattr(args, "ace_production_validation_mode", None) or ("assembly-only" if args.dry_run else "provider")
        if mode == "assembly-only" and not args.dry_run:
            print("ACE production rollout error: assembly-only requires --dry-run")
            return 2
        if mode == "provider" and args.dry_run:
            print("ACE production rollout error: provider validation cannot use --dry-run")
            return 2
        config = RolloutConfig(
            enabled=True,
            rollout_percent=percent,
            profile=args.profile,
            kill_switch=bool(getattr(args, "ace_production_kill_switch", False)),
            validation_mode=mode,
            target_chunk=max(1, int(args.ace_production_target_chunk)) if args.ace_production_target_chunk else None,
        )
        if getattr(args, "ace_production_resume_from_stage", None):
            if not config.target_chunk:
                print("ACE production rollout error: resume requires --ace-production-target-chunk")
                return 2
            plan = prepare_canary_resume(ROOT, source_stage=args.ace_production_resume_from_stage, target_stage=args.stage, target_chunk=config.target_chunk)
            if not plan.ready:
                print(f"ACE production rollout resume error: missing chunks {','.join(map(str, plan.missing_chunks))}")
                return 2
        _apply_runtime_timeout_env(args)
        _apply_provider_env(args)
        options = LiteraryRegressionOptions(
            root=ROOT, test_sets=_normalize_regression_sets(args.sets), stage_name=args.stage, profile=args.profile,
            chunk_size=max(300, args.chunk_size) if args.chunk_size is not None else 1000,
            chunk_size_explicit=args.chunk_size is not None, speed=args.speed, model=args.model, dry_run=args.dry_run,
            overwrite=args.overwrite, resume=not args.no_resume, max_retries=max(0, args.max_retries),
            provider_attempts=max(1, args.provider_attempts) if args.provider_attempts is not None else None,
            retry_base_seconds=max(0.0, args.retry_base_seconds), qa_fail_policy=args.qa_fail_policy,
            simplified_chinese_policy=args.simplified_chinese_policy, evaluate=not args.no_evaluate,
            previous_stage=args.previous_stage, progress_enabled=not getattr(args, "no_progress", False),
        )
        metrics = RolloutMetrics()
        controller = RollbackController()
        audit_path = _resolve(required["metrics"]).with_suffix(".jsonl")
        rollback_path = _resolve(required["rollback"])
        for reason in prior_rollback_reasons(rollback_path):
            controller.trigger(reason)
        stage_output = ROOT / "tests" / "literary" / "outputs" / args.stage
        resume_snapshot = frozenset() if args.overwrite else snapshot_resume_chunks(stage_output)
        with production_rollout_session(config, evidence, metrics=metrics, controller=controller, audit_path=audit_path):
            regression_result = run_literary_regression(options)
        provider_text = " ".join(
            str(value)
            for value in (
                regression_result.get("status", ""),
                regression_result.get("error", ""),
                *(record.get("error", "") for record in regression_result.get("records", ()) if isinstance(record, dict)),
            )
        ).lower()
        provider_status = "timeout" if "timeout" in provider_text else "503" if "503" in provider_text else "success"
        metrics.observe_provider(provider_status)
        outcome = collect_production_outcome(
            regression_result,
            metrics,
            root=ROOT,
            baseline_stage=args.previous_stage,
            resume_snapshot=resume_snapshot,
            provider_status=provider_status,
        )
        metrics.observe_quality_outcome(outcome)
        quality_inputs = rollback_quality_inputs(outcome)
        quality_evaluated = mode == "provider" and outcome.activated_chunks > 0
        if getattr(args, "ace_production_simulate_rollback", False):
            controller.trigger("rollback-simulation")
        rollback = evaluate_automatic_rollback(
            new_issues=quality_inputs.new_issues if quality_evaluated else (),
            quality_score=quality_inputs.quality_score if quality_evaluated else None,
            baseline_quality_score=quality_inputs.baseline_quality_score if quality_evaluated else None,
            qa_failure_rate=quality_inputs.qa_failure_rate if quality_evaluated else None,
            baseline_qa_failure_rate=quality_inputs.baseline_qa_failure_rate if quality_evaluated else None,
            provider_calls_added=metrics.provider_calls_added,
            anchor_mismatch=quality_inputs.anchor_mismatch,
            replacement_count=quality_inputs.replacement_count if outcome.activated_chunks else 1,
            metrics_complete=metrics.total_packages > 0,
            evidence_match=not evidence.blockers,
            kill_switch=config.kill_switch,
            artifact_integrity=evidence.evidence_integrity,
            provider_status=provider_status,
            quality_evidence_complete=outcome.evidence_complete if quality_evaluated else None,
        )
        if controller.disabled:
            rollback = RollbackDecision(rollback.version, True, "disabled", tuple(dict.fromkeys((*controller.reasons, *rollback.reasons))), rollback.provider_limitation)
        if rollback.rollback:
            controller.trigger(*rollback.reasons)
        metrics.observe_quality_rollback(evaluated=quality_evaluated, triggered=rollback.rollback, reasons=rollback.reasons)
        write_metrics_report(metrics, _resolve(required["metrics"]))
        rollback_path.parent.mkdir(parents=True, exist_ok=True)
        import json as _json
        rollback_path.write_text(_json.dumps(rollback.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"ace_production_metrics_report: {_resolve(required['metrics'])}")
        print(f"ace_production_rollback_report: {rollback_path}")
        print(f"ace_production_activated: {metrics.activated_packages}")
        print(f"ace_production_provider_limitation: {rollback.provider_limitation or 'none'}")
        if benchmark_enabled:
            _write_production_benchmark_run(
                args, regression_result, benchmark_mode, metrics.records, resume_snapshot,
                rollback_triggered=rollback.rollback,
            )
        base_rc = _print_regression_result(regression_result)
        return 1 if rollback.rollback else base_rc
    if bool(getattr(args, "ace_strategy_select_validate", False)):
        policy_path = _resolve(args.ace_strategy_policy_report) if args.ace_strategy_policy_report else get_te_v7_artifact_path(ROOT, "te_v7_stage081", TE_V7_STAGE081_PRODUCTION_ACTIVATION_POLICY)
        budget_path = _resolve(args.ace_strategy_budget_report) if args.ace_strategy_budget_report else get_te_v7_artifact_path(ROOT, "te_v7_stage082", TE_V7_STAGE082_PROFILE_AWARE_CONTEXT_BUDGET)
        out_path = _resolve(args.ace_strategy_report) if args.ace_strategy_report else get_te_v7_artifact_path(ROOT, "te_v7_stage083", TE_V7_STAGE083_ADAPTIVE_CONTEXT_STRATEGY_SELECTION)
        try:
            evidence = load_strategy_selection_evidence(policy_path, budget_path)
            decision = evaluate_strategy_selection(
                evidence,
                StrategySelectionRequest(
                    profile=args.profile,
                    explicitly_enabled=bool(args.ace_strategy_enable),
                    kill_switch=bool(args.ace_strategy_kill_switch),
                ),
            )
        except (OSError, ValueError, TypeError) as exc:
            print(f"ACE strategy selection error: {exc}")
            return 2
        write_strategy_selection_report(decision, out_path)
        print(f"ace_strategy_report: {out_path}")
        print(f"ace_strategy_status: {decision.status}")
        print(f"ace_strategy_ready: {str(decision.ready).lower()}")
        print(f"ace_strategy: {decision.strategy}")
        print(f"ace_strategy_profile: {decision.profile}")
        print(f"ace_strategy_rollout_percent: {decision.rollout_percent}")
        print(f"ace_strategy_context_tokens: {decision.effective_context_tokens}")
        print(f"ace_strategy_blockers: {','.join(decision.blockers) or 'none'}")
        return 0 if decision.ready else 1
    if bool(getattr(args, "ace_profile_budget_validate", False)):
        out_path = _resolve(args.ace_profile_budget_report) if args.ace_profile_budget_report else get_te_v7_artifact_path(ROOT, "te_v7_stage082", TE_V7_STAGE082_PROFILE_AWARE_CONTEXT_BUDGET)
        decision = evaluate_profile_budget(
            ProfileBudgetRequest(
                profile=args.profile,
                model_context_limit=int(args.ace_profile_budget_model_limit),
                fixed_prompt_tokens=int(args.ace_profile_budget_fixed_prompt_tokens),
                source_tokens=int(args.ace_profile_budget_source_tokens),
                reserved_output_tokens=int(args.ace_profile_budget_output_tokens),
                requested_context_tokens=args.ace_profile_budget_requested_tokens,
            )
        )
        write_profile_budget_report(decision, out_path)
        print(f"ace_profile_budget_report: {out_path}")
        print(f"ace_profile_budget_status: {decision.status}")
        print(f"ace_profile_budget_ready: {str(decision.ready).lower()}")
        print(f"ace_profile_budget_profile: {decision.profile}")
        print(f"ace_profile_budget_effective_tokens: {decision.effective_context_tokens}")
        print(f"ace_profile_budget_blockers: {','.join(decision.blockers) or 'none'}")
        print(f"ace_profile_budget_limitations: {','.join(decision.limitations) or 'none'}")
        return 0 if decision.ready else 1
    if bool(getattr(args, "ace_production_policy_validate", False)):
        ab_path = _resolve(args.ace_production_policy_ab_report) if args.ace_production_policy_ab_report else get_te_v7_artifact_path(ROOT, "te_v7_stage075", TE_V7_STAGE075_CANARY_AB_QUALITY_VALIDATION)
        canary_path = _resolve(args.ace_production_policy_canary_report) if args.ace_production_policy_canary_report else get_te_v7_artifact_path(ROOT, "te_v7_stage06", TE_V7_STAGE06_CANARY_PRODUCTION_VALIDATION)
        out_path = _resolve(args.ace_production_policy_report) if args.ace_production_policy_report else get_te_v7_artifact_path(ROOT, "te_v7_stage081", TE_V7_STAGE081_PRODUCTION_ACTIVATION_POLICY)
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
        path = _resolve(args.ace_canary_ab_report) if args.ace_canary_ab_report else get_te_v7_artifact_path(ROOT, "te_v7_stage075", TE_V7_STAGE075_CANARY_AB_QUALITY_VALIDATION)
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
        benchmark_resume_snapshot = frozenset()
        if benchmark_enabled and not args.overwrite:
            from core.adaptive_context_production_rollout import snapshot_resume_chunks as _snapshot
            raw = _snapshot(ROOT / "tests" / "literary" / "outputs" / args.stage)
            benchmark_resume_snapshot = frozenset((str(row.get("name", "")), index) for row in discover_test_sets(ROOT, options.test_sets) for _, index in raw)
        regression_result = run_literary_regression(options)
        if benchmark_enabled:
            _write_production_benchmark_run(args, regression_result, benchmark_mode, (), benchmark_resume_snapshot)
        return _print_regression_result(regression_result)

    if canary_validate:
        report_path = _resolve(args.ace_canary_report) if args.ace_canary_report else get_te_v7_artifact_path(ROOT, "te_v7_stage06", TE_V7_STAGE06_CANARY_PRODUCTION_VALIDATION)
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

    report_path = _resolve(args.ace_shadow_report) if args.ace_shadow_report else get_te_v7_artifact_path(ROOT, "te_v7_stage04", TE_V7_STAGE04_PRODUCTION_SHADOW_VALIDATION)
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
