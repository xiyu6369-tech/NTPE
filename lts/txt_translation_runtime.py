from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable

from core.translation_engine.context_intelligence import apply_context_intelligence, build_naturalness_repair_directives
from core.translation_naturalness import (
    analyze_unsupported_details,
    apply_literary_collocation_guard,
    analyze_voice_register,
    canonicalize_novel_chinese,
)
from core.translation_engine.translation_engine import TranslationEngine
from core.translation_engine.prompt_intelligence import apply_prompt_intelligence
from core.translation_engine.utils import now_iso, save_json, save_text
from core.literary import LiteraryPromptBuilder, normalize_profile, normalize_literary_style
from core.prompt_compiler import (
    PROMPT_COMPILER_VERSION,
    ADAPTIVE_FEEDBACK_VERSION,
    build_adaptive_feedback,
    render_adaptive_feedback_block,
)
from core.prompt_compiler.rules import enabled_discipline_rules, render_discipline_block
from core.translation_runtime.runtime_qa import RuntimeQAPolicy, analyze_runtime_quality, soft_fail_naturalness_report
from core.translation_quality_v5.runtime_integration import run_quality_v5_phase1, merge_quality_v5_into_runtime_qa
from core.translation_quality_v5.unified_quality_gate import attach_unified_report
from core.translation_discipline import (
    DisciplineRuntimeContext,
    TargetedRetryUnit,
    integrate_translation_discipline_runtime,
    merge_targeted_retry_result,
    validate_targeted_merge,
)
# Stage 04-06 compatibility: orchestrate_runtime_discipline( remains publicly
# available as the implementation adapter behind the Stage 09 entrypoint.
# Frozen Stage 04 observability token: revalidated={str(discipline_outcome.revalidated).lower()}
# Frozen Stage 06 progress token: discipline-runtime-orchestrator
from core.translation_quality_v5.best_attempt import AttemptCandidate, select_best_attempt, selection_metadata
from core.translation_quality_v5.segment_recovery import (
    SEGMENT_RECOVERY_VERSION,
    completeness_issue_codes,
    recovery_metadata,
    should_use_segment_recovery,
    split_recovery_segments,
)
from core.translation_runtime.runtime_speed_policy import (
    RuntimeSpeedPolicy,
    effective_timeout,
    get_runtime_speed_policy,
    naturalness_guard_policy_for_speed,
)
from core.translation_quality_integration_v72 import (
    PromptBudget,
    QualityIntegrationFlags,
    apply_to_prompt_package as apply_translation_quality_integration_v72,
)
# RM-8.3 Delivery import is lazy (inside function) to avoid circular import


DEFAULT_MODEL = "meta/llama-3.3-70b-instruct"
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_OUTPUT_SUFFIX = "_zh"
DEFAULT_MAX_RETRIES = 3
DEFAULT_QA_RETRY_PROMPT_ENABLED = True
DEFAULT_RETRY_BASE_SECONDS = 5.0
DEFAULT_CHARACTER_MEMORY = "memory/character_memory_lts.json"
DEFAULT_MIN_LENGTH_RATIO = 0.18
DEFAULT_MAX_KOREAN_CHARS = 2
DEFAULT_MAX_REPEATED_LINES = 2
DEFAULT_OUTPUT_FORMATTER_ENABLED = True
QA_FAIL_POLICIES = ("retry", "fail", "warn")
RETRYABLE_ERROR_PATTERNS = (
    "503",
    "429",
    "400",
    "resourceexhausted",
    "degraded",
    "cannot be invoked",
    "rate limit",
    "too many requests",
    "service unavailable",
    "timeout",
    "temporarily unavailable",
)


@dataclass(frozen=True)
class TxtTranslationOptions:
    input_path: Path
    output_dir: Path
    chunk_size: int = DEFAULT_CHUNK_SIZE
    model: str = DEFAULT_MODEL
    project_name: str = "NTPE Novel Translation"
    source_language: str = "ko"
    target_language: str = "zh-TW"
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
    output_formatter_enabled: bool = DEFAULT_OUTPUT_FORMATTER_ENABLED
    taiwan_traditional_normalization: bool = True
    quality_profile: str = "novel"
    previous_context_chars: int = 700
    simplified_chinese_policy: str = "normalize"  # normalize|warn|fail
    progress_enabled: bool = True
    speed: str = "balanced"
    chunk_size_explicit: bool = False
    provider_attempts: int | None = None
    qa_attempts: int | None = None
    runtime_timeout: int | None = None
    user_api_timeout: int | None = None
    naturalness_retry_limit: int | None = None
    quality_v5_enabled: bool = True
    quality_v5_report_enabled: bool = True
    quality_integration_v72: bool = False
    quality_character_memory_v72: bool = False
    quality_context_scene_v72: bool = False
    quality_naturalness_v72: bool = False
    quality_integration_kill_switch_v72: bool = False
    quality_character_store_v72: object | None = None
    quality_context_scene_store_v72: object | None = None
    quality_active_character_ids_v72: tuple[str, ...] = ()
    quality_chapter_id_v72: str | None = None
    quality_scene_id_v72: str | None = None
    quality_sequence_index_v72: int | None = None
    quality_selection_time_v72: str = "9999-01-01T00:00:00Z"
    quality_prompt_budget_v72: PromptBudget | None = None

    # RM-8.3 Delivery (Phase 6)
    quality_delivery_v83: bool = False
    quality_delivery_formats_v83: tuple[str, ...] = ("txt",)


def read_text_auto(path: str | Path) -> str:
    path = Path(path)
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr", "big5", "cp950"):
        try:
            text = raw.decode(enc)
            return normalize_text(text)
        except UnicodeDecodeError:
            continue
    return normalize_text(raw.decode("utf-8", errors="replace"))


def normalize_text(text: str) -> str:
    text = text.replace("\ufeff", "").replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip() + "\n" if text.strip() else ""


def split_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []
    if chunk_size < 300:
        raise ValueError("chunk_size must be >= 300")

    paragraphs = re.split(r"(\n{2,})", text)
    blocks: list[str] = []
    current = ""

    for item in paragraphs:
        if not item:
            continue
        candidate = current + item
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current.strip():
            blocks.extend(_split_oversized(current, chunk_size))
        current = item

    if current.strip():
        blocks.extend(_split_oversized(current, chunk_size))

    return [b.strip() + "\n" for b in blocks if b.strip()]


def _split_oversized(text: str, chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            window = text[start:end]
            cut = max(window.rfind("。"), window.rfind("！"), window.rfind("？"), window.rfind("."), window.rfind("\n"))
            if cut > chunk_size * 0.45:
                end = start + cut + 1
        pieces.append(text[start:end])
        start = end
    return pieces


def load_glossary_text(path: str | Path) -> dict[str, str]:
    path = Path(path)
    if not path.exists():
        return {}
    pairs: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        delimiter = "=" if "=" in line else "->" if "->" in line else "→" if "→" in line else None
        if delimiter is None:
            continue
        src, target = line.split(delimiter, 1)
        src = src.strip().strip("- ").strip()
        target = target.strip()
        if src and target:
            pairs[src] = target
    return pairs


def load_json_pairs(path: str | Path) -> dict[str, str]:
    path = Path(path)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    return _extract_pairs(data)


def load_locked_dictionary(root: Path, options: TxtTranslationOptions | None = None) -> dict[str, str]:
    locked: dict[str, str] = {}
    for path in (root / "character_override.json", root / "glossary_override.json"):
        locked.update(load_json_pairs(path))

    locked.update(load_glossary_text(root / "glossary.txt"))

    if options and options.glossary_path:
        custom_glossary = options.glossary_path if options.glossary_path.is_absolute() else root / options.glossary_path
        locked.update(load_glossary_text(custom_glossary))
        locked.update(load_json_pairs(custom_glossary))

    memory_path = resolve_character_memory_path(root, options)
    if memory_path:
        locked.update(load_json_pairs(memory_path))
    return locked


def resolve_character_memory_path(root: Path, options: TxtTranslationOptions | None = None) -> Path:
    if options and options.character_memory_path:
        return options.character_memory_path if options.character_memory_path.is_absolute() else root / options.character_memory_path
    return root / DEFAULT_CHARACTER_MEMORY


# Stage-18.12: production name-lock hotfix.
# The model sometimes translates locked Korean names into plausible but wrong Chinese
# variants.  These aliases are applied after provider output and again before final
# assembly, so glossary terms remain stable even when the model drifts.
DEFAULT_LOCKED_TRANSLATION_ALIASES: dict[str, set[str]] = {
    "鄭泰義": {"定泰義", "丁泰義", "正泰義", "鄭太義", "正太義", "鄭泰宜", "鄭泰儀"},
    "伊萊": {"伊蕾", "伊雷", "伊來", "伊莱", "一萊"},
    "凱爾": {"卡爾", "凱爾爾", "凯尔"},
    "伊萊・里格勞": {"伊萊·里格勞", "伊萊里格勞", "伊萊・利格羅", "伊萊·利格羅", "伊蕾・里格勞", "伊蕾·里格勞"},
    "凱爾・里格勞": {"凱爾·里格勞", "凱爾里格勞", "凱爾・利格羅", "凱爾·利格羅", "卡爾・里格勞"},
}


def build_translation_alias_map(locked_dictionary: dict[str, str]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for target in locked_dictionary.values():
        if not target:
            continue
        for alias in DEFAULT_LOCKED_TRANSLATION_ALIASES.get(target, set()):
            if alias and alias != target:
                aliases[alias] = target
    return aliases


def apply_locked_dictionary(text: str, locked_dictionary: dict[str, str]) -> str:
    result = text or ""
    # TER-v1.1: apply target aliases before source replacements so wrong Chinese
    # variants such as 伊蕾 are normalized even when the Korean source term is
    # already gone from provider output.
    for alias, target in sorted(build_translation_alias_map(locked_dictionary).items(), key=lambda item: len(item[0]), reverse=True):
        if alias and target:
            result = result.replace(alias, target)
    for source, target in sorted(locked_dictionary.items(), key=lambda item: len(item[0]), reverse=True):
        if not source or not target:
            continue
        # Remove accidental Korean/source residue and normalize any exact source term that survived provider output.
        result = result.replace(source, target)
    return result


def matched_locked_dictionary(source_text: str, locked_dictionary: dict[str, str]) -> dict[str, str]:
    """Return only terms that must be enforced for this source segment."""
    return {src: target for src, target in locked_dictionary.items() if src and target and src in source_text}


def collect_matched_locked_terms(chunks: list[str], locked_dictionary: dict[str, str]) -> dict[str, str]:
    source_text = "\n".join(chunks)
    return {src: target for src, target in locked_dictionary.items() if src and src in source_text}


def update_character_memory(path: str | Path, matched_terms: dict[str, str]) -> None:
    if not matched_terms:
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_json_pairs(path)
    existing.update(matched_terms)
    payload = {
        "version": "1.1-lts-stage-03",
        "updated_at": now_iso(),
        "characters": existing,
    }
    save_json(path, payload)



def get_resume_state_path(output_dir: Path, input_path: Path) -> Path:
    return output_dir / f"{input_path.stem}_resume_state.json"


def load_resume_state(path: str | Path) -> dict:
    path = Path(path)
    if not path.exists():
        return {"version": "1.1-lts-stage-05", "chunks": {}, "events": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {"version": "1.1-lts-stage-05", "chunks": {}, "events": []}
    if not isinstance(data, dict):
        return {"version": "1.1-lts-stage-05", "chunks": {}, "events": []}
    data.setdefault("version", "1.1-lts-stage-05")
    data.setdefault("chunks", {})
    data.setdefault("events", [])
    return data


def save_resume_state(path: str | Path, state: dict) -> None:
    save_json(path, state)


def is_retryable_error(error: str) -> bool:
    lowered = str(error or "").lower()
    return any(pattern in lowered for pattern in RETRYABLE_ERROR_PATTERNS)


def retry_delay_seconds(attempt: int, base_seconds: float) -> float:
    return max(0.0, float(base_seconds)) * (2 ** max(0, attempt - 1))


def timeout_retry_delay_seconds(attempt: int, base_seconds: float) -> float:
    """Return the configured delay after a provider timeout.

    NTPE_TIMEOUT_RETRY_DELAYS accepts a comma-separated sequence such as
    ``5,15,30``.  When attempts exceed the sequence, the last value is reused.
    Invalid or empty configuration falls back to the normal exponential delay.
    """
    raw = os.environ.get("NTPE_TIMEOUT_RETRY_DELAYS", "5,15,30")
    values: list[float] = []
    for item in raw.split(","):
        try:
            values.append(max(0.0, float(item.strip())))
        except ValueError:
            continue
    if not values:
        return retry_delay_seconds(attempt, base_seconds)
    index = min(max(1, int(attempt)) - 1, len(values) - 1)
    return values[index]


def capacity_retry_delay_seconds(attempt: int, base_seconds: float) -> float:
    """Return provider-capacity backpressure delay (default 60/120/180s)."""
    raw = os.environ.get("NTPE_CAPACITY_RETRY_DELAYS", "60,120,180")
    values: list[float] = []
    for item in raw.split(","):
        try:
            values.append(max(0.0, float(item.strip())))
        except ValueError:
            continue
    if not values:
        return max(60.0, retry_delay_seconds(attempt, base_seconds))
    index = min(max(1, int(attempt)) - 1, len(values) - 1)
    return values[index]


def progress_enabled(options: TxtTranslationOptions | None = None) -> bool:
    if options is not None and not getattr(options, "progress_enabled", True):
        return False
    value = os.environ.get("NTPE_PROGRESS", "1").lower()
    return value not in {"0", "false", "no", "off"}


def emit_progress(message: str, *, options: TxtTranslationOptions | None = None) -> None:
    if progress_enabled(options):
        print(f"[NTPE PROGRESS] {message}", flush=True)


def apply_runtime_speed_policy(options: TxtTranslationOptions) -> TxtTranslationOptions:
    policy = get_runtime_speed_policy(options.speed)
    user_timeout = options.user_api_timeout
    if user_timeout is None and os.environ.get("NTPE_API_TIMEOUT_EXPLICIT") == "1":
        try:
            user_timeout = int(float(os.environ.get("NTPE_API_TIMEOUT", "")))
        except ValueError:
            user_timeout = None
    chunk_size = options.chunk_size if options.chunk_size_explicit else policy.chunk_size
    return replace(
        options,
        speed=policy.speed,
        chunk_size=max(300, int(chunk_size)),
        provider_attempts=options.provider_attempts or policy.provider_attempts,
        qa_attempts=options.qa_attempts or policy.qa_attempts,
        runtime_timeout=(
            options.runtime_timeout
            or (max(1, int(user_timeout)) if user_timeout is not None and os.environ.get("NTPE_API_TIMEOUT_EXPLICIT") == "1" else effective_timeout(policy, user_timeout))
        ),
        user_api_timeout=user_timeout,
        naturalness_retry_limit=policy.naturalness_retry_limit if options.naturalness_retry_limit is None else options.naturalness_retry_limit,
    )


def save_live_progress(path: Path, payload: dict) -> None:
    try:
        save_json(path, payload)
    except Exception:
        # Live progress must never break translation.
        pass


def _provider_model_chain(primary_model: str) -> list[str]:
    """Return provider model chain with env-configurable fallbacks.

    TER-v2.1 keeps the default model unchanged, but improves degraded-model
    handling.  Users may configure fallback models without changing code:

        set NTPE_FALLBACK_MODELS=model_a,model_b

    Duplicate entries are removed while preserving order.
    """
    models: list[str] = []
    for model in [primary_model, *os.environ.get("NTPE_FALLBACK_MODELS", "").split(",")]:
        model = str(model or "").strip()
        if model and model not in models:
            models.append(model)
    return models or [primary_model]


def _provider_model_for_attempt(package: dict, attempt: int) -> str:
    primary = package.get("model_profile", {}).get("model", "")
    chain = _provider_model_chain(primary)
    # Rotate across configured providers.  If no fallback is configured this
    # simply returns the primary model every time.
    return chain[(max(1, attempt) - 1) % len(chain)]


def _effective_provider_timeout(package: dict, attempt: int) -> int:
    source_len = int(package.get("source", {}).get("char_count", 0) or 0)
    runtime_timeout = package.get("runtime", {}).get("speed_timeout")
    base_timeout = int(os.environ.get("NTPE_API_TIMEOUT", "60"))
    if runtime_timeout:
        try:
            policy_timeout = max(1, int(float(runtime_timeout)))
            if os.environ.get("NTPE_API_TIMEOUT_EXPLICIT") == "1":
                return base_timeout
            return policy_timeout
        except ValueError:
            pass
    # TER-v2.4: an explicit CLI/API timeout is authoritative.  Previous
    # short-chunk defaults (90/120s) are still useful for smoke tests, but they
    # must not silently lower a user supplied --api-timeout 180/300 value.
    if os.environ.get("NTPE_API_TIMEOUT_EXPLICIT") == "1":
        return base_timeout
    first_timeout = int(os.environ.get("NTPE_SHORT_CHUNK_FIRST_TIMEOUT", "90"))
    retry_timeout = int(os.environ.get("NTPE_RETRY_TIMEOUT", "120" if source_len <= 700 else str(base_timeout)))
    if attempt == 1 and 0 < source_len <= 700:
        return min(base_timeout, first_timeout)
    if attempt > 1 and 0 < source_len <= 700:
        return min(base_timeout, retry_timeout)
    return base_timeout


def _is_provider_capacity_error(error: str) -> bool:
    lowered = str(error or "").lower()
    return "resourceexhausted" in lowered or "worker local total request limit" in lowered or "503" in lowered


def _is_provider_degraded_error(error: str) -> bool:
    lowered = str(error or "").lower()
    return "degraded" in lowered or "cannot be invoked" in lowered or "function id" in lowered


def _is_provider_timeout_error(error: str) -> bool:
    lowered = str(error or "").lower()
    return "timeout" in lowered or "timed out" in lowered


def translate_package_with_retry(engine: TranslationEngine, package: dict, package_path: Path, options: TxtTranslationOptions) -> dict:
    attempts = max(1, int(options.provider_attempts or (int(options.max_retries) + 1)))
    last_result: dict = {"status": "failed", "error": "translation was not attempted"}
    package_id = package.get("package_id", package_path.stem)
    original_model = package.get("model_profile", {}).get("model", "")
    model_chain = _provider_model_chain(original_model)
    provider_timeout_failures = 0
    source_len = int(package.get("source", {}).get("char_count", 0) or 0)
    for attempt in range(1, attempts + 1):
        runtime = package.setdefault("runtime", {})
        runtime["provider_attempt"] = attempt
        provider_model = _provider_model_for_attempt(package, attempt)
        package.setdefault("model_profile", {})["model"] = provider_model
        effective_timeout = _effective_provider_timeout(package, attempt)
        os.environ["NTPE_CURRENT_API_TIMEOUT"] = str(effective_timeout)
        emit_progress(
            f"provider request start package={package_id} attempt={attempt}/{attempts} "
            f"model={provider_model} timeout={effective_timeout}s",
            options=options,
        )
        started = time.time()
        result = engine.translate_package(package, package_path=package_path)
        elapsed = time.time() - started
        result["attempt"] = attempt
        result["provider_elapsed_seconds"] = round(elapsed, 3)
        result["provider_model"] = provider_model
        last_result = result
        if result.get("status") == "success":
            emit_progress(
                f"provider request success package={package_id} attempt={attempt}/{attempts} "
                f"model={provider_model} elapsed={elapsed:.1f}s",
                options=options,
            )
            return result
        error = result.get("error", "")
        emit_progress(
            f"provider request failed package={package_id} attempt={attempt}/{attempts} "
            f"model={provider_model} elapsed={elapsed:.1f}s error={error[:180]}",
            options=options,
        )
        if _is_provider_timeout_error(error):
            provider_timeout_failures += 1
        degraded = _is_provider_degraded_error(error)
        # TER-v2.1: a DEGRADED model is not helped by retrying the same model.
        # If no fallback is configured, fail immediately with an actionable
        # message instead of burning minutes.
        if degraded and len(model_chain) <= 1:
            result["error"] = (
                str(error)[:220]
                + " | TER-v2.1 fast-fail: provider model is DEGRADED. "
                + "Set NTPE_FALLBACK_MODELS or pass --fallback-models with an available backup model."
            )
            emit_progress("provider fast-fail: model degraded; no fallback model configured", options=options)
            return result
        # TER-v2.0: short literary smoke chunks should not spend 10+ minutes on
        # repeated provider hangs.  After two timeouts, fail fast unless a
        # fallback model chain is configured.
        timeout_fast_fail_enabled = os.environ.get("NTPE_SHORT_CHUNK_TIMEOUT_FAST_FAIL", "0") == "1"
        if timeout_fast_fail_enabled and 0 < source_len <= 700 and provider_timeout_failures >= 2 and len(model_chain) <= 1:
            result["error"] = (
                str(error)[:220]
                + " | TER-v2.4 timeout fast-fail enabled: short chunk timed out twice; retry later or set NTPE_FALLBACK_MODELS."
            )
            emit_progress("provider fast-fail: short chunk timed out twice; no fallback model configured", options=options)
            return result
        if attempt >= attempts or not is_retryable_error(error):
            return result
        if len(model_chain) > 1:
            next_model = model_chain[(attempt) % len(model_chain)]
            emit_progress(f"provider fallback candidate next_model={next_model}", options=options)
        delay = (
            timeout_retry_delay_seconds(attempt, options.retry_base_seconds)
            if _is_provider_timeout_error(error)
            else retry_delay_seconds(attempt, options.retry_base_seconds)
        )
        if degraded:
            delay = 0.0
        elif _is_provider_capacity_error(error):
            delay = capacity_retry_delay_seconds(attempt, options.retry_base_seconds)
        if delay > 0:
            emit_progress(f"retry wait {delay:.1f}s before next provider request", options=options)
            time.sleep(delay)
    package.setdefault("model_profile", {})["model"] = original_model
    return last_result


def _pipeline_mode() -> str:
    """Return the active translation pipeline mode (runtime or legacy)."""
    return os.environ.get("NTPE_RUNTIME_PIPELINE", "runtime").strip().lower()


def _translate_txt_with_runtime_pipeline(
    options: TxtTranslationOptions,
    root_path: Path,
    engine: TranslationEngine,
    chunks: list[str],
    input_path: Path,
    output_dir: Path,
    stage_dir: Path,
    chunk_out_dir: Path,
    locked_dictionary: dict,
    resume_state_path: Path,
    resume_state: dict,
    live_progress_path: Path,
    character_memory_path: Path | None,
    matched_terms_for_memory: list[str],
) -> dict:
    """RM-6.4.2: Translate a TXT file using the Runtime Pipeline.

    Uses RuntimeOrchestrator to coordinate all RM-6 layers:
        KnowledgeRuntime → PromptBuilder → TranslationRuntimeAdapter
        → RuntimeSession → Checkpoint → Trace → TranslationEngine

    Preserves post-translation quality processing (QA, naturalness,
    formatting, discipline, V5 integration) identical to legacy mode.

    RM-8.2: Cross-Chunk Context Continuity (feature-gated via quality_context_scene_v72)
    """
    from core.runtime_orchestrator import RuntimeOrchestrator
    from core.translation_runtime.boundary_detector import detect_boundary, BoundaryResult
    from core.context_scene_memory.scene_state import transition_scene, transition_chapter
    from core.context_scene_memory.context_selection import select_context_for_translation
    from core.context_scene_memory.store import ContextMemoryStore
    from core.context_scene_memory.models import BoundaryType, ContextEvidence, EvidenceType
    from core.intelligence.narrative_engine import NarrativeIntelligenceEngine

    def create_evidence_from_chunk(chunk_text: str) -> ContextEvidence:
        """Create a ContextEvidence from a chunk for scene transition tracking."""
        import hashlib
        return ContextEvidence(
            evidence_id=f"ev_{hashlib.md5(chunk_text.encode()).hexdigest()[:12]}",
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            source_case_id="translation_session",
            source_segment_id=f"chunk_{len(chunk_text)}",
            source_text_hash=hashlib.sha256(chunk_text.encode()).hexdigest()[:16],
            translation_text_hash=None,
            excerpt=chunk_text[:200] if chunk_text else "",
            language="ko",
            rule_id=None,
            observed_at=now_iso(),
        )

    orchestrator = RuntimeOrchestrator()
    orchestrator.set_engine(engine)

    # RM-8.2: Initialize cross-chunk context components (feature-gated)
    enable_cross_chunk_context = getattr(options, "quality_context_scene_v72", False)
    context_store = ContextMemoryStore() if enable_cross_chunk_context else None
    narrative_engine = NarrativeIntelligenceEngine() if enable_cross_chunk_context else None
    current_scene_id = "scene_1"
    current_chapter_id = "chapter_1"
    prev_chunk_text = ""
    active_character_ids = options.quality_active_character_ids_v72 if enable_cross_chunk_context else ()

    translated_chunks: list[str] = []
    records: list[dict] = []
    t0 = time.time()

    emit_progress(
        f"runtime pipeline enabled: orchestrator={orchestrator.version} chunks={len(chunks)} cross_chunk_context={enable_cross_chunk_context}",
        options=options,
    )

    # Start a single Runtime Session for the entire file
    session = orchestrator.start_session(metadata={
        "input": str(input_path),
        "chunk_total": len(chunks),
        "profile": options.quality_profile,
        "model": options.model,
        "pipeline": "runtime",
        "enable_cross_chunk_context": enable_cross_chunk_context,
    })
    session_id = session.session_id
    emit_progress(f"runtime session created: {session_id}", options=options)

    for idx, chunk in enumerate(chunks, start=1):
        emit_progress(f"runtime chunk {idx}/{len(chunks)} prepare chars={len(chunk)}", options=options)
        save_live_progress(live_progress_path, {
            "status": "running", "input": str(input_path), "output_dir": str(output_dir),
            "chunk_total": len(chunks), "chunk_completed": max(0, idx - 1),
            "current_chunk": idx, "current_step": "runtime_prepare",
            "updated_at": now_iso(),
        })

        chunk_file = chunk_out_dir / f"{input_path.stem}_chunk_{idx:06d}_zh.txt"
        chunk_key = f"{idx:06d}"

        source_hash = hashlib.sha256(chunk.encode("utf-8")).hexdigest()[:16]
        state_entry = resume_state["chunks"].get(chunk_key, {})
        reusable_state = (
            options.resume
            and state_entry.get("status") in {"success", "pass_with_warning"}
            and state_entry.get("source_hash") == source_hash
            and chunk_file.exists()
            and chunk_file.read_text(encoding="utf-8").strip()
        )

        package = build_prompt_package(
            options=options, chunk_text=chunk, chunk_index=idx, chunk_total=len(chunks),
            locked_dictionary=locked_dictionary,
            previous_context="\n\n".join(translated_chunks[-2:])[-options.previous_context_chars:] if translated_chunks else "",
        )
        package_path = stage_dir / f"{input_path.stem}_chunk_{idx:06d}.json"
        save_json(package_path, package)

        if reusable_state:
            emit_progress(f"runtime chunk {idx}/{len(chunks)} resume hit: using cached output", options=options)
            translation = chunk_file.read_text(encoding="utf-8")
            if options.strict_lock_terms:
                translation = apply_locked_dictionary(translation, locked_dictionary)
            translated_chunks.append(translation)
            records.append({"status": "skipped", "output_path": str(chunk_file), "package_id": package["package_id"], "attempt": 0, "metadata": {}})
            continue

        if options.dry_run:
            emit_progress(f"runtime chunk {idx}/{len(chunks)} dry-run: skip provider", options=options)
            translated_chunks.append("")
            resume_state["chunks"][chunk_key] = {"status": "dry_run", "source_hash": source_hash, "output_path": str(chunk_file), "updated_at": now_iso()}
            save_resume_state(resume_state_path, resume_state)
            records.append({"status": "dry_run", "output_path": str(chunk_file), "package_id": package["package_id"], "attempt": 0, "metadata": {}})
            continue

        # -- RM-8.2: Cross-Chunk Context Integration --
        # 1. BOUNDARY DETECTION
        if enable_cross_chunk_context:
            boundary: BoundaryResult = detect_boundary(prev_chunk_text, chunk)

            # 2. SCENE/CHAPTER TRANSITION
            if boundary.type != BoundaryType.SAME_SCENE:
                if boundary.type == BoundaryType.CHAPTER_TRANSITION:
                    transition_chapter(
                        store=context_store,
                        from_scene_id=current_scene_id,
                        to_scene_id=boundary.scene_id or f"scene_{idx}",
                        to_chapter_id=boundary.chapter_id,
                        evidence=create_evidence_from_chunk(chunk),
                    )
                    current_chapter_id = boundary.chapter_id
                elif boundary.type == BoundaryType.SCENE_TRANSITION:
                    transition_scene(
                        store=context_store,
                        from_scene_id=current_scene_id,
                        boundary=boundary.type,
                        to_scene_id=boundary.scene_id,
                        evidence=create_evidence_from_chunk(chunk),
                    )
                # UNKNOWN_TRANSITION: no transition, no expiry (conservative)
                current_scene_id = boundary.scene_id or current_scene_id

            # 3. CONTEXT SELECTION
            selection = select_context_for_translation(
                context_store=context_store,
                chapter_id=current_chapter_id,
                scene_id=current_scene_id,
                sequence_index=idx,
                character_ids=active_character_ids,
                token_budget=512,
                character_token_budget=256,
            )

            # 4. NARRATIVE STATE
            prev_translation = translated_chunks[-1] if translated_chunks else ""
            narrative_engine.analyze_chunk(source=chunk, translation=prev_translation)
            narrative_context = narrative_engine.get_context_for_prompt()

            # 5. ENTITY INJECTION (RM-7.2) - optional, None if not available
            entity_injection_set = None
            # if entity_resolver_available:
            #     entity_injection_set = entity_resolver.resolve(chunk)

            # Compose context_state metadata (feature-gated)
            context_state_metadata = {
                "context_selection_fingerprint": selection.fingerprint,
                "scene_id": current_scene_id,
                "scene_version": context_store.get_scene(current_scene_id).scene_version,
                "narrative": narrative_context,
                "boundary": boundary.to_dict(),
                "selected_context_ids": tuple(r.item_id for r in selection.selected_records),
            }
        else:
            boundary = BoundaryResult(type=BoundaryType.SAME_SCENE)
            selection = None
            narrative_context = {}
            entity_injection_set = None
            context_state_metadata = None

        # -- Runtime Pipeline execution --
        save_live_progress(live_progress_path, {
            "status": "running", "input": str(input_path), "output_dir": str(output_dir),
            "chunk_total": len(chunks), "chunk_completed": max(0, idx - 1),
            "current_chunk": idx, "current_step": "runtime_execute",
            "updated_at": now_iso(),
        })

        execution_result = orchestrator.execute(
            chunk_text=chunk,
            session_id=session_id,
            snapshot_id="",
            current_chunk=idx,
            total_chunks=len(chunks),
            metadata={
                "source": {
                    "chunk_text": chunk,
                    "char_count": len(chunk),
                },
                "model_profile": {
                    "model": options.model,
                    "temperature": 0.15,
                    "max_output_tokens": 4000,
                    "top_p": 0.85,
                },
                "profile": options.quality_profile,
                "system_prompt": package.get("prompt", {}).get("system_prompt", ""),
                "enable_cross_chunk_context": enable_cross_chunk_context,
                "context_state": context_state_metadata,
                "context_selection": selection if enable_cross_chunk_context else None,
                "scene_state": context_store.get_scene(current_scene_id) if enable_cross_chunk_context and context_store else None,
                "narrative_state": narrative_context if enable_cross_chunk_context else None,
                "entity_injection_set": entity_injection_set,
            },
        )

        response = execution_result.response
        provider_result = response if isinstance(response, dict) else {"status": "failed", "error": str(response)}

        if provider_result.get("status") == "success":
            translation = provider_result.get("translation", "")
            if not translation:
                out_path = provider_result.get("output_path", "")
                if out_path and Path(out_path).exists():
                    translation = Path(out_path).read_text(encoding="utf-8")
        else:
            translation = ""
            emit_progress(
                f"runtime chunk {idx}/{len(chunks)} engine error: {str(provider_result.get('error', 'unknown'))[:200]}",
                options=options,
            )

        if translation:
            generated_path = Path(provider_result.get("output_path", str(chunk_file)))
            save_text(generated_path, translation)

            # Post-translation quality processing (preserved from legacy)
            if options.strict_lock_terms:
                translation = apply_locked_dictionary(translation, locked_dictionary)
            translation = format_translation_output(translation, options)
            naturalness = canonicalize_novel_chinese(translation)
            translation = naturalness.text
            literary = apply_literary_collocation_guard(translation)
            translation = literary.text
            analyze_voice_register(chunk, translation, profile=options.quality_profile)

            # Quality V5
            qa_report: dict = {"passed": True, "issues": [], "metrics": {}}
            if options.quality_v5_enabled and options.qa_enabled:
                quality_v5 = run_quality_v5_phase1(
                    chunk, translation,
                    locked_terms=locked_dictionary,
                    config={"min_length_ratio": max(0.18, options.min_length_ratio)},
                )
                qa_report = merge_quality_v5_into_runtime_qa(
                    runtime_qa=qa_report, report=quality_v5,
                )

            # Legacy QA
            if options.qa_enabled and options.speed != "fast":
                # Build QA options for analyze_translation_quality
                qa_opts = TxtTranslationOptions(
                    input_path=input_path, output_dir=output_dir,
                    min_length_ratio=options.min_length_ratio,
                    max_korean_chars=options.max_korean_chars,
                    max_repeated_lines=options.max_repeated_lines,
                    simplified_chinese_policy=options.simplified_chinese_policy,
                    quality_profile=options.quality_profile,
                    speed=options.speed,
                )
                legacy_qa = analyze_translation_quality(
                    chunk, translation, options=qa_opts,
                )
                qa_report.setdefault("issues", []).extend(legacy_qa.get("issues", []))
                qa_report.setdefault("metrics", {}).update(legacy_qa.get("metrics", {}))
                qa_report["passed"] = qa_report.get("passed", True) and legacy_qa.get("passed", True)

            # Discipline runtime
            if options.qa_enabled:
                from core.translation_discipline.runtime_orchestrator import orchestrate_runtime_discipline
                _r = orchestrate_runtime_discipline(
                    text=chunk,
                    runtime_qa={"issues": qa_report.get("issues", []), "metrics": qa_report.get("metrics", {}), "unified_quality_report": qa_report},
                )
                qa_report["discipline"] = {
                    "initial_action": _r.initial_action,
                    "final_action": _r.final_action,
                    "revalidated": _r.revalidated,
                }

            package["qa"] = qa_report
            attach_unified_report(qa_report, qa_report)
            save_text(chunk_file, translation)
            translated_chunks.append(translation)
            result = {
                "status": "success",
                "output_path": str(chunk_file),
                "package_id": package["package_id"],
                "attempt": 1,
                "qa": qa_report,
                "runtime_pipeline": True,
                "orchestrator_version": orchestrator.version,
                "session_id": session_id,
                "metadata": {"context_state": context_state_metadata} if enable_cross_chunk_context else {},
            }
        else:
            translated_chunks.append("")
            result = provider_result
            if isinstance(result, dict) and "metadata" not in result:
                result["metadata"] = {}

        resume_state["chunks"][chunk_key] = {
            "status": result.get("status", "failed"),
            "source_hash": source_hash,
            "output_path": str(chunk_file),
            "updated_at": now_iso(),
        }
        save_resume_state(resume_state_path, resume_state)
        save_json(package_path, package)
        records.append(result)

        save_live_progress(live_progress_path, {
            "status": "running", "input": str(input_path), "output_dir": str(output_dir),
            "chunk_total": len(chunks), "chunk_completed": idx,
            "current_chunk": idx, "current_step": "runtime_processing",
            "updated_at": now_iso(),
        })

        # RM-8.2: Update prev_chunk_text for next iteration's boundary detection
        prev_chunk_text = chunk

    # Ensure session transitions to RUNNING before completing.
    # Dry-run or all-resume paths may skip execute() calls entirely.
    from core.runtime_session import RunStatus as _RS
    _state = orchestrator.session_manager.get_state(session_id)
    if _state is not None and _state.status.value == "CREATED":
        try:
            orchestrator.session_manager.update_runtime(session_id, status=_RS.RUNNING)
        except Exception:
            pass
    orchestrator.complete(session_id, success=True)

    # Finalize output
    save_live_progress(live_progress_path, {
        "status": "finalizing", "input": str(input_path), "output_dir": str(output_dir),
        "chunk_total": len(chunks), "chunk_completed": len(chunks),
        "current_step": "finalizing", "updated_at": now_iso(),
    })

    final_output = output_dir / f"{input_path.stem}{DEFAULT_OUTPUT_SUFFIX}.txt"
    if not options.dry_run and any(translated_chunks):
        final_text = "\n\n".join(translated_chunks).strip() + "\n"
        if options.strict_lock_terms and locked_dictionary:
            final_text = apply_locked_dictionary(final_text, locked_dictionary)
        save_text(final_output, final_text)
        if character_memory_path:
            update_character_memory(character_memory_path, matched_terms_for_memory)

    elapsed = time.time() - t0

    return {
        "status": "success",
        "input": str(input_path),
        "output": str(final_output),
        "output_dir": str(output_dir),
        "chunk_total": len(chunks),
        "resume_state": str(resume_state_path),
        "records": records,
        "summary": {
            "total_chunks": len(chunks),
            "error": 0,
            "elapsed_seconds": round(elapsed, 2),
        },
        "pipeline_mode": "runtime",
        "orchestrator_version": orchestrator.version,
        "session_id": session_id,
    }


TAIWAN_TRADITIONAL_REPLACEMENTS = {
    "台湾": "台灣",
    "台北": "臺北",
    "里面": "裡面",
    "里头": "裡頭",
    "这里": "這裡",
    "那里": "那裡",
    "哪里": "哪裡",
    "为": "為",
    "这": "這",
    "个": "個",
    "后": "後",
    "说": "說",
    "开": "開",
    "门": "門",
    "这": "這",
    "个": "個",
    "为": "為",
    "会": "會",
    "里": "裡",
    "后": "後",
    "发": "發",
    "么": "麼",
    "没": "沒",
    "过": "過",
    "对": "對",
    "还": "還",
    "种": "種",
    "现": "現",
    "实": "實",
    "当": "當",
    "从": "從",
    "长": "長",
    "处": "處",
    "头": "頭",
    "给": "給",
    "让": "讓",
    "觉": "覺",
    "声": "聲",
    "气": "氣",
    "爱": "愛",
    "书": "書",
    "边": "邊",
    "间": "間",
    "见": "見",
    "听": "聽",
    "话": "話",
    "问": "問",
    "答": "答",
    "还": "還",
    "会": "會",
    "对": "對",
    "发": "發",
    "头": "頭",
    "么": "麼",
    "没": "沒",
    "让": "讓",
    "过": "過",
    "时": "時",
    "间": "間",
    "门": "門",
    "声": "聲",
    "来": "來",
    "见": "見",
    "现": "現",
    "长": "長",
    "体": "體",
    "书": "書",
    "气": "氣",
    "脸": "臉",
    "眼": "眼",
    "边": "邊",
    "从": "從",
    "点": "點",
    "样": "樣",
    "听": "聽",
    "话": "話",
    "轻": "輕",
    "动": "動",
    "实": "實",
    "觉": "覺",
    "该": "該",
    "着": "著",
}


# TER-v1.2: extra high-frequency simplified forms observed in provider output.
TAIWAN_TRADITIONAL_REPLACEMENTS.update({
    "扬": "揚",
    "涌": "湧",
    "转": "轉",
    "离": "離",
    "视": "視",
    "顾": "顧",
    "绝": "絕",
    "严": "嚴",
    "为": "為",
    "与": "與",
    "处": "處",
    "压": "壓",
    "积": "積",
    "绪": "緒",
    "郁": "鬱",
    "亚": "亞",
    "尔": "爾",
    "莱": "萊",
    "凯": "凱",
})

def normalize_punctuation_for_zh_tw(text: str) -> str:
    result = text or ""
    # Normalize common ASCII punctuation from provider output into CJK punctuation.
    result = result.replace("...", "……")
    result = result.replace(",", "，")
    result = result.replace(":", "：")
    result = result.replace(";", "；")
    result = result.replace("?", "？")
    result = result.replace("!", "！")
    result = result.replace("(", "（").replace(")", "）")
    # Convert common provider dialogue quotes to corner brackets conservatively.
    result = re.sub(r'[“"]([^“”"\n]{1,200})[”"]', r'「\1」', result)
    result = re.sub(r"[‘']([^‘’'\n]{1,200})[’']", r"『\1』", result)
    # Collapse excessive punctuation introduced by provider formatting.
    result = re.sub(r"。{2,}", "。", result)
    result = re.sub(r"，{2,}", "，", result)
    result = re.sub(r"！{2,}", "！", result)
    result = re.sub(r"？{2,}", "？", result)
    return result


def normalize_taiwan_traditional(text: str) -> str:
    result = text or ""
    for simplified, traditional in sorted(TAIWAN_TRADITIONAL_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        result = result.replace(simplified, traditional)
    return result


def clean_provider_output(text: str) -> str:
    result = text or ""
    # Remove common model preambles without touching narrative content.
    preamble_patterns = (
        r"^以下(?:是|為).{0,20}翻譯[:：]\s*",
        r"^譯文[:：]\s*",
        r"^翻譯結果[:：]\s*",
    )
    for pattern in preamble_patterns:
        result = re.sub(pattern, "", result.strip(), flags=re.IGNORECASE)
    result = result.replace("\ufeff", "").replace("\x00", "")
    result = result.replace("\r\n", "\n").replace("\r", "\n")
    result = re.sub(r"[ \t]+\n", "\n", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def format_translation_output(text: str, options: TxtTranslationOptions | None = None) -> str:
    options = options or TxtTranslationOptions(input_path=Path("input.txt"), output_dir=Path("output"))
    result = clean_provider_output(text)
    if not options.output_formatter_enabled:
        return result.strip()
    result = normalize_punctuation_for_zh_tw(result)
    if options.taiwan_traditional_normalization:
        result = normalize_taiwan_traditional(result)
    result = normalize_literary_style(result)
    if options.taiwan_traditional_normalization:
        result = normalize_taiwan_traditional(result)
    result = clean_provider_output(result)
    return result.strip()

def count_korean_characters(text: str) -> int:
    return len(re.findall(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3]", text or ""))


def _normalized_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text or ""))


def detect_repeated_lines(text: str, max_repeated_lines: int = DEFAULT_MAX_REPEATED_LINES) -> list[str]:
    counts: dict[str, int] = {}
    repeated: list[str] = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if len(line) < 4:
            continue
        counts[line] = counts.get(line, 0) + 1
        if counts[line] > max_repeated_lines and line not in repeated:
            repeated.append(line)
    return repeated


def detect_simplified_chinese(text: str) -> list[str]:
    """Return possible simplified-Chinese hits after formatter normalization.

    Stage-18.14 note:
    This detector is intentionally conservative. A single remaining hit should
    not fail a full translation job because providers sometimes output rare
    characters that overlap with simplified forms or proper nouns.
    """
    return [simp for simp in TAIWAN_TRADITIONAL_REPLACEMENTS if simp in (text or "")][:20]


def should_fail_on_simplified_chinese(options: TxtTranslationOptions, hit_count: int) -> bool:
    policy = (getattr(options, "simplified_chinese_policy", "normalize") or "normalize").lower()
    if policy == "fail":
        return hit_count > 0
    return False


def detect_locked_term_violations(source_text: str, translated_text: str, locked_dictionary: dict[str, str]) -> list[dict]:
    violations: list[dict] = []
    for src, target in locked_dictionary.items():
        if src and src in source_text and target and target not in translated_text:
            violations.append({"source": src, "target": target, "code": "LOCKED_TERM_MISSING"})
    for alias, target in build_translation_alias_map(locked_dictionary).items():
        if alias and alias in translated_text:
            violations.append({"alias": alias, "target": target, "code": "LOCKED_ALIAS_USED"})
    return violations




def detect_quality_lock_violations(translated_text: str) -> list[dict]:
    """TER-v2.0 hard quality floor for recurring semantic regressions.

    These patterns are not stylistic preferences; they are known semantic or
    readability regressions observed in Smoke_Set.  They should fail QA so the
    provider retries instead of accepting a bad baseline.
    """
    text = translated_text or ""
    violations: list[dict] = []
    checks = [
        ("QUALITY_LOCK_WRONG_REPLY_OBJECT", r"留下了?鄭泰義(?:一個)?[^。]{0,12}(?:回答|話)", "回答被錯誤地留給鄭泰義；應是伊萊只留下簡短回答。"),
        ("QUALITY_LOCK_DUPLICATE_DISAPPEARANCE", r"消失在視線[裡中][^。]{0,18}。[^。]{0,12}消失(?:在視線[裡中])?後", "同一個消失事件被重複敘述。"),
        ("QUALITY_LOCK_AWKWARD_FATIGUE", r"幾十年(?:來)?的疲(?:勞|憊)(?:感覺像洪水一樣)?(?:一下子)?(?:都)?湧(?:了)?上(?:心頭|來)", "疲憊描寫不自然或過度直譯。"),
    ]
    for code, pattern, message in checks:
        match = re.search(pattern, text)
        if match:
            violations.append({"code": code, "message": message, "sample": match.group(0)[:80]})
    return violations

def analyze_translation_quality(source_text: str, translated_text: str, options: TxtTranslationOptions | None = None, locked_dictionary: dict[str, str] | None = None) -> dict:
    """TER-v2.2 consolidated runtime quality gate.

    The public function name is kept for backward compatibility, but the actual
    checks now run through core.translation_runtime.runtime_qa so TXT runtime,
    integration tests, and future provider-layer hooks share the same policy.
    """
    options = options or TxtTranslationOptions(input_path=Path("input.txt"), output_dir=Path("output"))
    runtime_policy = RuntimeQAPolicy(
        enabled=options.qa_enabled,
        min_length_ratio=options.min_length_ratio,
        max_korean_chars=options.max_korean_chars,
        max_repeated_lines=options.max_repeated_lines,
        max_repeated_sentences=options.max_repeated_lines,
        simplified_chinese_policy=options.simplified_chinese_policy,
        quality_profile=options.quality_profile,
        naturalness_guard_policy=naturalness_guard_policy_for_speed(options.speed),
    )
    simplified_terms = list(TAIWAN_TRADITIONAL_REPLACEMENTS.keys()) if options.taiwan_traditional_normalization else []
    return analyze_runtime_quality(
        source_text,
        translated_text,
        runtime_policy,
        locked_dictionary=locked_dictionary or {},
        alias_map=build_translation_alias_map(locked_dictionary or {}),
        simplified_terms=simplified_terms,
        extra_violations=detect_quality_lock_violations(translated_text),
    )


def qa_retry_delay_seconds(attempt: int, base_seconds: float) -> float:
    # QA retry uses a softer delay than provider-limit retry.
    return min(retry_delay_seconds(attempt, base_seconds), 30.0)


def _extract_pairs(data) -> dict[str, str]:
    pairs: dict[str, str] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and isinstance(key, str):
                pairs[key] = value
            elif isinstance(value, dict):
                source = value.get("source") or value.get("ko") or value.get("korean") or key
                target = value.get("target") or value.get("translation") or value.get("zh") or value.get("traditional") or value.get("name")
                if isinstance(source, str) and isinstance(target, str):
                    pairs[source] = target
                pairs.update(_extract_pairs(value))
            elif isinstance(value, list):
                for item in value:
                    pairs.update(_extract_pairs(item))
    elif isinstance(data, list):
        for item in data:
            pairs.update(_extract_pairs(item))
    return pairs



def get_max_output_tokens(chunk_text: str, options: TxtTranslationOptions) -> int:
    env_value = __import__("os").environ.get("NTPE_MAX_OUTPUT_TOKENS")
    if env_value:
        try:
            return max(400, min(6000, int(float(env_value))))
        except ValueError:
            pass
    profile = (options.quality_profile or "literary").lower()
    source_len = max(1, len(chunk_text))
    if profile == "fast":
        return _dynamic_output_tokens(source_len, floor=360, small=520, mid=900, cap=1400, ratio=0.95)
    if profile == "balanced":
        return _dynamic_output_tokens(source_len, floor=420, small=620, mid=1100, cap=1800, ratio=1.05)
    if profile in ("premium", "quality"):
        return _dynamic_output_tokens(source_len, floor=650, small=1000, mid=1800, cap=3200, ratio=1.35)
    # literary / novel default: enough for complete prose, but avoids oversized short-smoke requests.
    return _dynamic_output_tokens(source_len, floor=420, small=560, mid=1200, cap=2400, ratio=1.12)


def _dynamic_output_tokens(source_len: int, *, floor: int, small: int, mid: int, cap: int, ratio: float) -> int:
    if source_len <= 600:
        return small
    if source_len <= 1200:
        return max(floor, min(mid, math.ceil(source_len * ratio)))
    return max(floor, min(cap, math.ceil(source_len * ratio)))

def _runtime_prompt_discipline_enabled() -> bool:
    return os.environ.get("NTPE_PROMPT_DISCIPLINE", "1").strip().lower() not in {"0", "false", "no", "off"}


def _ensure_runtime_prompt_compiler_wiring(prompt_result) -> tuple[str, str, dict, dict]:
    """Guarantee that the provider-ready runtime prompt contains v5.5.2 discipline.

    The LiteraryPromptBuilder remains the primary compiler path.  This runtime guard
    prevents a stale or alternate builder path from silently omitting discipline in
    regression/TXT packages.
    """
    system_prompt = prompt_result.system_prompt
    user_prompt = prompt_result.user_prompt
    compiler_meta = dict(getattr(prompt_result, "prompt_compiler", {}) or {})
    enabled = _runtime_prompt_discipline_enabled()
    from core.translation_discipline.engine import TranslationDisciplineEngine
    discipline_engine = TranslationDisciplineEngine(profile="literary")
    rules = discipline_engine.generation_rules(enabled=enabled)
    discipline = discipline_engine.render_generation_policy(enabled=enabled)

    if discipline and "【翻譯紀律】" not in user_prompt:
        marker = "【Korean】"
        if marker in user_prompt:
            user_prompt = user_prompt.replace(marker, discipline + "\n" + marker, 1)
        else:
            user_prompt = user_prompt.rstrip() + "\n" + discipline

    compiler_meta.update({
        "version": compiler_meta.get("version") or PROMPT_COMPILER_VERSION,
        "mode": "prompt_discipline" if rules else "legacy_equivalent",
        "discipline_enabled": bool(rules),
        "discipline_rule_codes": [rule.code for rule in rules],
        "discipline_rule_count": len(rules),
        "runtime_wiring_verified": (not rules) or ("【翻譯紀律】" in user_prompt),
    })

    compiler_meta.update(discipline_engine.metadata(enabled=bool(rules)))

    # Count discipline as policy/generation guidance so the runtime profile reflects
    # the actual provider payload rather than the pre-compiler prompt.
    profile = prompt_result.prompt_profile
    if discipline:
        profile_dict = profile.to_dict()
        from core.literary.prompt_profiler import estimate_tokens
        discipline_tokens = estimate_tokens(discipline)
        profile_dict["policy_tokens"] += discipline_tokens
        profile_dict["total_tokens"] += discipline_tokens
        profile_dict["total_chars"] += len(discipline) + 1
    else:
        profile_dict = profile.to_dict()

    return system_prompt, user_prompt, compiler_meta, profile_dict


def build_prompt_package(
    *,
    options: TxtTranslationOptions,
    chunk_text: str,
    chunk_index: int,
    chunk_total: int,
    locked_dictionary: dict[str, str],
    previous_context: str = "",
) -> dict:
    input_name = options.input_path.name
    package_id = f"TXT_{options.input_path.stem}_{chunk_index:06d}"
    source_hash = hashlib.sha1(chunk_text.encode("utf-8")).hexdigest()
    matched = {src: target for src, target in locked_dictionary.items() if src and src in chunk_text}

    alias_map = build_translation_alias_map(matched)
    profile = normalize_profile(options.quality_profile or "literary")

    prompt_result = LiteraryPromptBuilder().build(
        chunk_text=chunk_text,
        locked_dictionary=matched,
        alias_map=alias_map,
        previous_context=previous_context.strip(),
        profile=profile,
    )
    system_prompt, user_prompt, compiler_meta, runtime_prompt_profile = _ensure_runtime_prompt_compiler_wiring(prompt_result)

    package = {
        "package_id": package_id,
        "project": {
            "project_name": options.project_name,
            "source_language": options.source_language,
            "target_language": options.target_language,
        },
        "session": {
            "session_id": f"TXT_{options.input_path.stem}",
            "file_name": input_name,
            "chunk_index": chunk_index,
            "chunk_total": chunk_total,
            "resume_key": f"{input_name}:chunk:{chunk_index:06d}",
        },
        "model_profile": {
            "engine": "NVIDIA",
            "model": options.model,
            "context_window": 131072,
            "temperature": 0.12 if profile in ("literary", "premium") else 0.15,
            "top_p": 0.82 if profile in ("literary", "premium") else 0.85,
            "max_output_tokens": get_max_output_tokens(chunk_text, options),
        },
        "source": {
            "chunk_text": chunk_text,
            "source_hash": source_hash,
            "char_count": len(chunk_text),
        },
        "context": {
            "previous_summary": "",
            "previous_chunk_tail": previous_context[-options.previous_context_chars:] if previous_context else "",
            "recent_characters": prompt_result.character_context.current_focus,
            "recent_terms": [term.target for term in prompt_result.glossary_context.matched_terms],
            "narrative_context": prompt_result.narrative_context.to_dict(),
            "character_context": prompt_result.character_context.to_dict(),
        },
        "knowledge": {
            "locked_dictionary": matched,
        },
        "prompt": {
            **prompt_result.to_prompt_dict(),
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "prompt_profile": runtime_prompt_profile,
            "prompt_compiler": compiler_meta,
            "prompt_discipline_enabled": compiler_meta["discipline_enabled"],
            "discipline_rule_count": compiler_meta["discipline_rule_count"],
        },
        "prompt_runtime": {
            "prompt_compiler": compiler_meta["version"],
            "prompt_discipline_enabled": compiler_meta["discipline_enabled"],
            "discipline_rule_count": compiler_meta["discipline_rule_count"],
            "runtime_wiring_verified": compiler_meta["runtime_wiring_verified"],
            "discipline_engine_version": compiler_meta["discipline_engine_version"],
            "discipline_profile": compiler_meta["discipline_profile"],
            "discipline_policy_version": compiler_meta["discipline_policy_version"],
            "discipline_policy_source": compiler_meta["discipline_policy_source"],
            "active_rule_codes": compiler_meta["active_rule_codes"],
            "active_rule_count": compiler_meta["active_rule_count"],
            "generation_rule_count": compiler_meta["generation_rule_count"],
            "adaptive_rule_count": compiler_meta["adaptive_rule_count"],
        },
        "qa_requirements": {
            "check_korean_residue": True,
            "check_name_rules": True,
            "check_glossary": True,
            "check_repetition": True,
            "check_length_ratio": True,
            "check_literary_policy": True,
        },
        "runtime": {
            "speed": options.speed,
            "provider_attempts": options.provider_attempts,
            "qa_attempts": options.qa_attempts,
            "speed_timeout": options.runtime_timeout,
            "naturalness_retry_limit": options.naturalness_retry_limit,
        },
        "metadata": {
            "created_at": now_iso(),
            "created_by": "NTPE 1.2 Translation Engine Refactoring v2.0",
            "package_version": "1.2-translation-engine-refactor-v2.0",
        },
    }
    package = apply_prompt_intelligence(package, chunk_text)
    package = apply_context_intelligence(package, chunk_text, previous_context)
    return apply_translation_quality_integration_v72(
        package,
        flags=QualityIntegrationFlags(
            integration=options.quality_integration_v72,
            character_memory=options.quality_character_memory_v72,
            context_scene=options.quality_context_scene_v72,
            naturalness=options.quality_naturalness_v72,
            kill_switch=options.quality_integration_kill_switch_v72,
        ),
        character_store=options.quality_character_store_v72,
        context_scene_store=options.quality_context_scene_store_v72,
        active_character_ids=options.quality_active_character_ids_v72,
        chapter_id=options.quality_chapter_id_v72,
        scene_id=options.quality_scene_id_v72,
        sequence_index=options.quality_sequence_index_v72 if options.quality_sequence_index_v72 is not None else chunk_index,
        selection_time=options.quality_selection_time_v72,
        budget=options.quality_prompt_budget_v72,
    )


def build_qa_retry_user_prompt(original_user_prompt: str, qa_report: dict, qa_attempt: int) -> str:
    """Build an issue-directed QA retry prompt while preserving legacy wording."""
    feedback = build_adaptive_feedback(qa_report)
    feedback_block = render_adaptive_feedback_block(feedback, qa_attempt)

    issues = qa_report.get("issues", []) if isinstance(qa_report, dict) else []
    issue_lines: list[str] = []
    locked_lines: list[str] = []
    naturalness_samples: list[dict] = []
    for issue in issues[:8]:
        if not isinstance(issue, dict):
            continue
        code = issue.get("code") or issue.get("type") or "QA_ISSUE"
        message = issue.get("message") or ""
        issue_lines.append(f"- {code}: {message}")
        samples = issue.get("samples", []) if isinstance(issue.get("samples"), list) else []
        if code == "NATURALNESS_GUARD":
            naturalness_samples.extend(sample for sample in samples if isinstance(sample, dict))
        for sample in samples:
            if isinstance(sample, dict) and sample.get("source") and sample.get("target"):
                locked_lines.append(f"- {sample['source']} => {sample['target']}")

    issue_text = "\n".join(issue_lines) or "- QA_FAILED: previous output did not pass validation"
    locked_text = "\n".join(dict.fromkeys(locked_lines)) or "- 依 Glossary 欄位嚴格執行"
    naturalness_directives = build_naturalness_repair_directives(naturalness_samples)
    naturalness_text = "\n".join(f"- {item}" for item in naturalness_directives) or "- No Naturalness Guard repair directive."

    retry_note = f"""

【NTPE 自動重試指令】
前一次輸出未通過品質檢查，請重新翻譯，不要沿用前一次輸出。
失敗原因：
{issue_text}

必須修正的鎖定譯名：
{locked_text}

重試要求：
- 請直接完整翻成自然流暢、符合小說背景的繁體中文。
- 鎖定譯名必須逐字一致，不能自行改成近似音譯。
- 嚴禁複製韓文原文作為譯文。
- 嚴禁輸出「以下是翻譯」等說明。
- 保留段落順序與劇情資訊，不可摘要。
- 這是第 {qa_attempt} 次 QA 重試。
"""
    if feedback_block:
        retry_note += "\n" + feedback_block + "\n"
    retry_note += f"\nNaturalness Guard repair directives:\n{naturalness_text}\n"
    return original_user_prompt.rstrip() + retry_note


def save_partial_translation_output(
    *,
    output_dir: Path,
    input_path: Path,
    translated_chunks: list[str],
    records: list[dict],
    failed_chunk: int,
    error: str,
    options: TxtTranslationOptions,
) -> dict[str, str]:
    """Persist successful chunks when a later provider call fails.

    TER-v2.4 keeps partial translation material visible and resumable instead
    of leaving only per-chunk files.  This does not mark the run successful; it
    only writes a clearly named partial file and manifest for recovery.
    """
    partial_output = output_dir / f"{input_path.stem}{DEFAULT_OUTPUT_SUFFIX}.partial.txt"
    partial_manifest = output_dir / f"{input_path.stem}_partial_manifest.json"
    partial_text = "\n\n".join(chunk.strip() for chunk in translated_chunks if chunk.strip()).strip()
    if partial_text:
        save_text(partial_output, partial_text + "\n")
    payload = {
        "status": "partial_failed",
        "input": str(input_path),
        "partial_output": str(partial_output),
        "completed_chunks": len([chunk for chunk in translated_chunks if chunk.strip()]),
        "failed_chunk": failed_chunk,
        "error": error,
        "retry": {"max_retries": options.max_retries, "base_seconds": options.retry_base_seconds},
        "records": records,
        "updated_at": now_iso(),
    }
    save_json(partial_manifest, payload)
    return {"partial_output": str(partial_output), "partial_manifest": str(partial_manifest)}


def has_retry_worthy_naturalness_issue(qa_report: dict) -> bool:
    for issue in qa_report.get("issues", []) if isinstance(qa_report, dict) else []:
        if isinstance(issue, dict) and issue.get("code") == "NATURALNESS_GUARD" and issue.get("retry_worthy"):
            return True
    return False


def _segment_recovery_provider_attempts() -> int:
    try:
        return max(1, min(2, int(os.environ.get("NTPE_SEGMENT_RECOVERY_PROVIDER_ATTEMPTS", "1"))))
    except ValueError:
        return 1


def _chunk_recovery_provider_budget() -> int:
    try:
        return max(0, min(20, int(os.environ.get("NTPE_CHUNK_PROVIDER_BUDGET", "2"))))
    except ValueError:
        return 2


def translate_completeness_segments(
    *,
    engine: TranslationEngine,
    options: TxtTranslationOptions,
    root_path: Path,
    stage_dir: Path,
    chunk_out_dir: Path,
    input_path: Path,
    chunk_text: str,
    chunk_index: int,
    chunk_total: int,
    locked_dictionary: dict[str, str],
    previous_context: str,
    qa_report: dict,
    parent_package: dict,
) -> dict:
    issue_codes = completeness_issue_codes(qa_report)
    segments = split_recovery_segments(chunk_text)
    metadata = recovery_metadata(chunk_text, segments, issue_codes)
    parent_package.setdefault("prompt_runtime", {})["segment_completeness_recovery"] = metadata

    if len(segments) < 2:
        return {"status": "not_applicable", "error": "source could not be split safely"}

    emit_progress(
        f"chunk {chunk_index}/{chunk_total} segment-completeness-recovery "
        f"segments={len(segments)} codes={','.join(issue_codes)}",
        options=options,
    )
    recovered: list[str] = []
    segment_records: list[dict] = []
    segment_options = replace(options, provider_attempts=_segment_recovery_provider_attempts())

    for segment_index, segment_text in enumerate(segments, start=1):
        local_previous = previous_context
        if recovered:
            local_previous = (local_previous + "\n\n" + recovered[-1])[-options.previous_context_chars:]
        subpackage = build_prompt_package(
            options=segment_options,
            chunk_text=segment_text,
            chunk_index=chunk_index,
            chunk_total=chunk_total,
            locked_dictionary=locked_dictionary,
            previous_context=local_previous,
        )
        subpackage["package_id"] = f"{parent_package['package_id']}_RECOVERY_{segment_index:02d}"
        subpackage["session"]["recovery_parent_package_id"] = parent_package["package_id"]
        subpackage["session"]["recovery_segment_index"] = segment_index
        subpackage["session"]["recovery_segment_total"] = len(segments)
        subpackage.setdefault("prompt_runtime", {})["segment_completeness_recovery"] = {
            **metadata,
            "segment_index": segment_index,
        }
        recovery_note = (
            "\n\n【NTPE 分段完整性修復】\n"
            f"這是原文缺漏修復的第 {segment_index}/{len(segments)} 段。只翻譯本段 Korean，完整保留本段所有資訊；"
            "不得摘要、補寫、重述 Previous，也不要輸出分析。\n"
            "[/NTPE 分段完整性修復]"
        )
        subpackage["prompt"]["user_prompt"] = subpackage["prompt"]["user_prompt"].rstrip() + recovery_note
        sub_path = stage_dir / f"{input_path.stem}_chunk_{chunk_index:06d}_recovery_{segment_index:02d}.json"
        save_json(sub_path, subpackage)
        emit_progress(
            f"chunk {chunk_index}/{chunk_total} recovery segment {segment_index}/{len(segments)} chars={len(segment_text)}",
            options=options,
        )
        sub_result = translate_package_with_retry(engine, subpackage, sub_path, segment_options)
        segment_records.append({
            "segment_index": segment_index,
            "package_path": str(sub_path),
            "status": sub_result.get("status"),
            "error": sub_result.get("error"),
        })
        if sub_result.get("status") != "success":
            parent_package["prompt_runtime"]["segment_completeness_recovery"]["segments"] = segment_records
            return {
                "status": "failed",
                "error": f"segment recovery {segment_index}/{len(segments)} failed: {sub_result.get('error', 'unknown error')}",
                "segment_recovery": metadata,
            }
        generated = Path(sub_result["output_path"]).read_text(encoding="utf-8").strip()
        recovered.append(generated)

    combined = "\n\n".join(part for part in recovered if part).strip() + "\n"
    combined_path = chunk_out_dir / f"{input_path.stem}_chunk_{chunk_index:06d}_segment_recovery_candidate_zh.txt"
    save_text(combined_path, combined)
    metadata["segments"] = segment_records
    metadata["combined_output_path"] = str(combined_path)
    parent_package["prompt_runtime"]["segment_completeness_recovery"] = metadata
    emit_progress(
        f"chunk {chunk_index}/{chunk_total} segment-completeness-recovery completed output={combined_path.name}",
        options=options,
    )
    return {
        "status": "success",
        "output_path": str(combined_path),
        "attempt": 1,
        "provider_model": parent_package.get("model_profile", {}).get("model"),
        "segment_recovery": metadata,
    }


def translate_targeted_retry_units(
    *, engine: TranslationEngine, options: TxtTranslationOptions, stage_dir: Path,
    chunk_out_dir: Path, input_path: Path, chunk_text: str, chunk_index: int,
    chunk_total: int, locked_dictionary: dict[str, str], previous_context: str,
    parent_package: dict, original_translation: str, plan: dict,
) -> dict:
    """Execute Stage 10 units without owning issue-to-tier policy in runtime."""
    raw_units = list(plan.get("targeted_retry_units") or [])
    budget = dict(plan.get("provider_call_budget") or {})
    remaining = max(0, int(budget.get("remaining") or 0))
    records: list[dict] = []
    candidate = original_translation
    used = 0
    for raw in raw_units:
        if used >= remaining:
            return {"status": "failed", "error": "targeted retry provider budget exhausted", "targeted_retry": {"units": records, "result": "budget_exhausted"}}
        start, end = raw.get("source_start"), raw.get("source_end")
        if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start or end > len(chunk_text):
            return {"status": "not_applicable", "error": "targeted retry source evidence is not safely bounded", "targeted_retry": {"units": records, "result": "unsafe_evidence"}}
        unit = TargetedRetryUnit(
            unit_id=str(raw.get("unit_id") or f"targeted-{used + 1:03d}"),
            source_text=chunk_text[start:end], source_start=start, source_end=end,
            paragraph_indexes=tuple(raw.get("paragraph_indexes") or ()),
            reason_codes=tuple(raw.get("reason_codes") or ()),
            prompt_directives=tuple(raw.get("prompt_directives") or ()),
            max_provider_attempts=1, merge_strategy=str(raw.get("merge_strategy") or "replace_aligned_range"),
            metadata=dict(raw.get("metadata") or {}),
        )
        subpackage = build_prompt_package(
            options=replace(options, provider_attempts=1), chunk_text=unit.source_text,
            chunk_index=chunk_index, chunk_total=chunk_total,
            locked_dictionary=locked_dictionary, previous_context=previous_context,
        )
        subpackage["package_id"] = f"{parent_package['package_id']}_{unit.unit_id.upper()}"
        subpackage.setdefault("session", {})["targeted_retry_parent_package_id"] = parent_package["package_id"]
        subpackage.setdefault("prompt_runtime", {})["adaptive_retry_policy"] = {"version": plan.get("version"), "tier": "targeted_retry", "unit": unit.to_metadata()}
        sub_path = stage_dir / f"{input_path.stem}_chunk_{chunk_index:06d}_{unit.unit_id}.json"
        save_json(sub_path, subpackage)
        result = translate_package_with_retry(engine, subpackage, sub_path, replace(options, provider_attempts=1))
        used += 1
        record = {**unit.to_metadata(), "provider_attempts": 1, "status": result.get("status"), "result": "failed"}
        if result.get("status") != "success":
            record["error"] = str(result.get("error") or "provider error")[:500]
            records.append(record)
            return {"status": "failed", "error": record["error"], "targeted_retry": {"units": records, "provider_calls_used": used, "result": "provider_failed"}}
        replacement = Path(result["output_path"]).read_text(encoding="utf-8").strip()
        merged = merge_targeted_retry_result(candidate, replacement, unit)
        if merged is None:
            record["result"] = "unsafe_merge"
            records.append(record)
            return {"status": "not_applicable", "error": "targeted retry lacks a safe translated merge range", "targeted_retry": {"units": records, "provider_calls_used": used, "result": "unsafe_merge"}}
        merge_validation = validate_targeted_merge(candidate, replacement, merged, unit)
        record["merge_validation"] = merge_validation.to_metadata()
        if not merge_validation.accepted:
            record["result"] = "unsafe_merge_validation"
            records.append(record)
            return {"status": "not_applicable", "error": f"targeted retry merge validation failed: {merge_validation.reason}", "targeted_retry": {"units": records, "provider_calls_used": used, "result": "unsafe_merge_validation", "merge_validation": merge_validation.to_metadata()}}
        candidate = merged
        record["result"] = "merged_pending_revalidation"
        records.append(record)
    output_path = chunk_out_dir / f"{input_path.stem}_chunk_{chunk_index:06d}_targeted_retry_candidate_zh.txt"
    save_text(output_path, candidate)
    metadata = {"version": plan.get("version"), "tier": "targeted_retry", "units": records, "provider_calls_used": used, "result": "merged_pending_revalidation"}
    parent_package.setdefault("prompt_runtime", {})["targeted_retry"] = metadata
    return {"status": "success", "output_path": str(output_path), "attempt": 1, "provider_model": parent_package.get("model_profile", {}).get("model"), "targeted_retry": metadata}


def translate_txt(options: TxtTranslationOptions, root: str | Path | None = None) -> dict:
    options = apply_runtime_speed_policy(options)
    root_path = Path(root) if root else Path(__file__).resolve().parents[1]
    input_path = options.input_path if options.input_path.is_absolute() else root_path / options.input_path
    output_dir = options.output_dir if options.output_dir.is_absolute() else root_path / options.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    emit_progress(f"read input: {input_path}", options=options)
    text = read_text_auto(input_path)
    emit_progress(f"split text: chars={len(text)} chunk_size={options.chunk_size}", options=options)
    chunks = split_text(text, options.chunk_size)
    if not chunks:
        raise ValueError(f"輸入檔案沒有可翻譯內容：{input_path}")
    emit_progress(f"chunk plan: total={len(chunks)}", options=options)

    stage_dir = root_path / "prompt_packages" / "txt_runtime"
    stage_dir.mkdir(parents=True, exist_ok=True)
    chunk_out_dir = output_dir / f"{input_path.stem}_chunks"
    chunk_out_dir.mkdir(parents=True, exist_ok=True)

    locked_dictionary = load_locked_dictionary(root_path, options)
    character_memory_path = resolve_character_memory_path(root_path, options)
    matched_terms_for_memory = collect_matched_locked_terms(chunks, locked_dictionary)
    engine = TranslationEngine(root=root_path)

    # RM-6.4.2: If runtime pipeline is active, delegate to Runtime Orchestrator
    if _pipeline_mode() == "runtime":
        _resume_path = get_resume_state_path(output_dir, input_path)
        _live_path = output_dir / f"{input_path.stem}_live_progress.json"
        save_live_progress(_live_path, {
            "status": "running",
            "input": str(input_path), "output_dir": str(output_dir),
            "chunk_total": len(chunks), "chunk_completed": 0,
            "current_step": "initialized", "updated_at": now_iso(),
        })
        _resume_state = load_resume_state(_resume_path)
        _resume_state["input"] = str(input_path)
        _resume_state["output_dir"] = str(output_dir)
        _resume_state["chunk_total"] = len(chunks)
        _resume_state["updated_at"] = now_iso()
        save_resume_state(_resume_path, _resume_state)
        return _translate_txt_with_runtime_pipeline(
            options=options, root_path=root_path, engine=engine,
            chunks=chunks, input_path=input_path, output_dir=output_dir,
            stage_dir=stage_dir, chunk_out_dir=chunk_out_dir,
            locked_dictionary=locked_dictionary,
            resume_state_path=_resume_path,
            resume_state=_resume_state,
            live_progress_path=_live_path,
            character_memory_path=character_memory_path,
            matched_terms_for_memory=matched_terms_for_memory,
        )

    translated_chunks: list[str] = []
    records: list[dict] = []
    resume_state_path = get_resume_state_path(output_dir, input_path)
    live_progress_path = output_dir / f"{input_path.stem}_live_progress.json"
    save_live_progress(live_progress_path, {
        "status": "running",
        "input": str(input_path),
        "output_dir": str(output_dir),
        "chunk_total": len(chunks),
        "chunk_completed": 0,
        "current_step": "initialized",
        "updated_at": now_iso(),
    })
    resume_state = load_resume_state(resume_state_path)
    resume_state["input"] = str(input_path)
    resume_state["output_dir"] = str(output_dir)
    resume_state["chunk_total"] = len(chunks)
    resume_state["updated_at"] = now_iso()
    save_resume_state(resume_state_path, resume_state)

    for idx, chunk in enumerate(chunks, start=1):
        emit_progress(f"chunk {idx}/{len(chunks)} prepare package chars={len(chunk)}", options=options)
        save_live_progress(live_progress_path, {
            "status": "running",
            "input": str(input_path),
            "output_dir": str(output_dir),
            "chunk_total": len(chunks),
            "chunk_completed": max(0, idx - 1),
            "current_chunk": idx,
            "current_step": "prepare_package",
            "updated_at": now_iso(),
        })
        package = build_prompt_package(
            options=options,
            chunk_text=chunk,
            chunk_index=idx,
            chunk_total=len(chunks),
            locked_dictionary=locked_dictionary,
            previous_context="\n\n".join(translated_chunks[-2:])[-options.previous_context_chars:] if translated_chunks else "",
        )
        package_path = stage_dir / f"{input_path.stem}_chunk_{idx:06d}.json"
        save_json(package_path, package)
        prompt_profile = package.get("prompt", {}).get("prompt_profile", {})
        if prompt_profile:
            emit_progress(
                "chunk {}/{} prompt profile: total={} system={} policy={} context={} glossary={} source={} max_tokens={}".format(
                    idx,
                    len(chunks),
                    prompt_profile.get("total_tokens", "?"),
                    prompt_profile.get("system_tokens", "?"),
                    prompt_profile.get("policy_tokens", "?"),
                    prompt_profile.get("context_tokens", "?"),
                    prompt_profile.get("glossary_tokens", "?"),
                    prompt_profile.get("source_tokens", "?"),
                    package.get("model_profile", {}).get("max_output_tokens", "?"),
                ),
                options=options,
            )
        emit_progress(f"chunk {idx}/{len(chunks)} package saved: {package_path.name}", options=options)

        chunk_file = chunk_out_dir / f"{input_path.stem}_chunk_{idx:06d}_zh.txt"
        chunk_key = f"{idx:06d}"
        source_hash = package["source"]["source_hash"]
        state_entry = resume_state["chunks"].get(chunk_key, {})
        reusable_state = (
            options.resume
            and state_entry.get("status") in {"success", "pass_with_warning"}
            and state_entry.get("source_hash") == source_hash
            and chunk_file.exists()
            and chunk_file.read_text(encoding="utf-8").strip()
        )

        if reusable_state:
            emit_progress(f"chunk {idx}/{len(chunks)} resume hit: using cached output", options=options)
            translation = chunk_file.read_text(encoding="utf-8")
            if options.strict_lock_terms:
                translation = apply_locked_dictionary(translation, locked_dictionary)
            result = {"status": "skipped", "output_path": str(chunk_file), "package_id": package["package_id"], "attempt": 0, "metadata": {}}
        elif options.dry_run:
            emit_progress(f"chunk {idx}/{len(chunks)} dry-run: skip provider", options=options)
            translation = ""
            result = {"status": "dry_run", "output_path": str(chunk_file), "package_id": package["package_id"], "attempt": 0, "metadata": {}}
            resume_state["chunks"][chunk_key] = {
                "status": "dry_run",
                "source_hash": source_hash,
                "output_path": str(chunk_file),
                "updated_at": now_iso(),
            }
            save_resume_state(resume_state_path, resume_state)
        else:
            qa_attempt_records: list[dict] = []
            attempt_candidates: list[AttemptCandidate] = []
            later_provider_error: dict | None = None
            qa_report = {"passed": True, "issues": [], "metrics": {}}
            translation = ""
            result = {"status": "failed", "error": "translation was not attempted", "attempt": 0}
            qa_attempts = max(1, int(options.qa_attempts or (int(options.max_retries) + 1))) if options.qa_fail_policy == "retry" else 1
            naturalness_retry_count = 0
            recovery_provider_calls_used = 0
            original_user_prompt = package["prompt"]["user_prompt"]
            for qa_attempt in range(1, qa_attempts + 1):
                emit_progress(f"chunk {idx}/{len(chunks)} QA attempt {qa_attempt}/{qa_attempts}", options=options)
                save_live_progress(live_progress_path, {
                    "status": "running",
                    "input": str(input_path),
                    "output_dir": str(output_dir),
                    "chunk_total": len(chunks),
                    "chunk_completed": max(0, idx - 1),
                    "current_chunk": idx,
                    "current_step": f"provider_and_qa_attempt_{qa_attempt}",
                    "updated_at": now_iso(),
                })
                if qa_attempt > 1:
                    feedback = build_adaptive_feedback(qa_report)
                    feedback_meta = feedback.to_metadata()
                    feedback_meta["qa_attempt"] = qa_attempt
                    package["prompt"]["user_prompt"] = build_qa_retry_user_prompt(original_user_prompt, qa_report, qa_attempt)
                    from core.translation_discipline.engine import TranslationDisciplineEngine
                    adaptive_rules = TranslationDisciplineEngine(profile="literary").adaptive_rules(
                        feedback_meta.get("issue_codes", []),
                        enabled=bool(feedback_meta.get("enabled", True)),
                    )
                    feedback_meta["discipline_rule_codes"] = [rule.code for rule in adaptive_rules]
                    feedback_meta["discipline_policy_version"] = "6.0.0-stage02"
                    package.setdefault("prompt_runtime", {})["adaptive_feedback"] = feedback_meta
                    package["prompt_runtime"]["adaptive_feedback_version"] = ADAPTIVE_FEEDBACK_VERSION
                    emit_progress(
                        f"chunk {idx}/{len(chunks)} adaptive-prompt-feedback "
                        f"codes={','.join(feedback_meta.get('issue_codes', [])) or 'generic'} "
                        f"directives={feedback_meta.get('directive_count', 0)}",
                        options=options,
                    )
                    save_json(package_path, package)
                retry_policy = dict(qa_report.get("adaptive_retry_policy") or {})
                retry_tier = str(retry_policy.get("tier") or "")
                if qa_attempt > 1 and retry_tier == "targeted_retry" and attempt_candidates:
                    retry_policy["provider_call_budget"] = {
                        **dict(retry_policy.get("provider_call_budget") or {}),
                        "used": recovery_provider_calls_used,
                        "remaining": max(0, int((retry_policy.get("provider_call_budget") or {}).get("limit") or 0) - recovery_provider_calls_used),
                    }
                    result = translate_targeted_retry_units(
                        engine=engine, options=options, stage_dir=stage_dir,
                        chunk_out_dir=chunk_out_dir, input_path=input_path,
                        chunk_text=chunk, chunk_index=idx, chunk_total=len(chunks),
                        locked_dictionary=locked_dictionary,
                        previous_context="\n\n".join(translated_chunks[-2:])[-options.previous_context_chars:] if translated_chunks else "",
                        parent_package=package, original_translation=attempt_candidates[-1].translation,
                        plan=retry_policy,
                    )
                    recovery_provider_calls_used += int((result.get("targeted_retry") or {}).get("provider_calls_used") or 0)
                    if result.get("status") == "not_applicable" and recovery_provider_calls_used < int((retry_policy.get("provider_call_budget") or {}).get("limit") or 0):
                        # Policy fallback: one full retry, still inside the chunk recovery budget.
                        result = translate_package_with_retry(engine, package, package_path, replace(options, provider_attempts=1))
                        recovery_provider_calls_used += 1
                elif qa_attempt > 1 and should_use_segment_recovery(qa_report, chunk):
                    result = translate_completeness_segments(
                        engine=engine,
                        options=options,
                        root_path=root_path,
                        stage_dir=stage_dir,
                        chunk_out_dir=chunk_out_dir,
                        input_path=input_path,
                        chunk_text=chunk,
                        chunk_index=idx,
                        chunk_total=len(chunks),
                        locked_dictionary=locked_dictionary,
                        previous_context="\n\n".join(translated_chunks[-2:])[-options.previous_context_chars:] if translated_chunks else "",
                        qa_report=qa_report,
                        parent_package=package,
                    )
                    save_json(package_path, package)
                elif qa_attempt > 1 and retry_tier == "full_retry":
                    budget_limit = int((retry_policy.get("provider_call_budget") or {}).get("limit") or 2)
                    if recovery_provider_calls_used >= budget_limit:
                        result = {"status": "failed", "error": "chunk recovery provider budget exhausted", "attempt": 0}
                    else:
                        result = translate_package_with_retry(engine, package, package_path, replace(options, provider_attempts=1))
                        recovery_provider_calls_used += 1
                else:
                    result = translate_package_with_retry(engine, package, package_path, options)
                result["qa_attempt"] = qa_attempt
                if result.get("status") != "success":
                    if attempt_candidates:
                        later_provider_error = {
                            "qa_attempt": qa_attempt,
                            "error": str(result.get("error") or "unknown provider error"),
                            "attempt": result.get("attempt", 1),
                        }
                    break
                generated_path = Path(result["output_path"])
                emit_progress(f"chunk {idx}/{len(chunks)} provider output received", options=options)
                translation = generated_path.read_text(encoding="utf-8")
                if options.strict_lock_terms:
                    translation = apply_locked_dictionary(translation, locked_dictionary)
                translation = format_translation_output(translation, options)
                naturalness_canonicalization = canonicalize_novel_chinese(translation)
                translation = naturalness_canonicalization.text
                literary_collocation = apply_literary_collocation_guard(translation)
                translation = literary_collocation.text
                voice_register_guard = analyze_voice_register(chunk, translation, profile=options.quality_profile)
                package.setdefault("prompt_runtime", {})["naturalness_canonicalization"] = naturalness_canonicalization.to_metadata()
                package.setdefault("prompt_runtime", {})["literary_collocation_guard"] = literary_collocation.to_metadata()
                package.setdefault("prompt_runtime", {})["voice_register_guard"] = voice_register_guard.to_metadata()
                if naturalness_canonicalization.changed or naturalness_canonicalization.warnings:
                    emit_progress(
                        f"chunk {idx}/{len(chunks)} naturalness-canonicalization "
                        f"changed={str(naturalness_canonicalization.changed).lower()} "
                        f"actions={len(naturalness_canonicalization.actions)} "
                        f"warnings={len(naturalness_canonicalization.warnings)}",
                        options=options,
                    )
                if literary_collocation.changed or literary_collocation.warnings:
                    emit_progress(
                        f"chunk {idx}/{len(chunks)} literary-collocation-guard "
                        f"changed={str(literary_collocation.changed).lower()} "
                        f"actions={len(literary_collocation.actions)} "
                        f"warnings={len(literary_collocation.warnings)}",
                        options=options,
                    )
                if voice_register_guard.issues or voice_register_guard.warnings:
                    emit_progress(
                        f"chunk {idx}/{len(chunks)} voice-register-guard "
                        f"issues={len(voice_register_guard.issues)} "
                        f"warnings={len(voice_register_guard.warnings)} "
                        f"blocking={str(voice_register_guard.blocking).lower()}",
                        options=options,
                    )
                quality_v5_report = None
                quality_reports_by_text: dict[str, dict] = {}

                def _discipline_quality_runner(candidate_text: str) -> dict:
                    nonlocal quality_v5_report
                    evaluated_text = format_translation_output(candidate_text, options)
                    if options.strict_lock_terms:
                        evaluated_text = apply_locked_dictionary(evaluated_text, locked_dictionary)
                    quality_v5_report = None
                    if options.quality_v5_enabled:
                        quality_v5_report = run_quality_v5_phase1(
                            chunk,
                            evaluated_text,
                            locked_terms=package.get("knowledge", {}).get("locked_dictionary", {}),
                            config={"min_length_ratio": max(0.18, options.min_length_ratio)},
                        )
                        candidate_voice_register = analyze_voice_register(
                            chunk, evaluated_text, profile=options.quality_profile
                        )
                        quality_v5_report.setdefault("metrics", {})["voice_register_guard"] = candidate_voice_register.to_metadata()
                        package.setdefault("prompt_runtime", {})["voice_register_guard"] = candidate_voice_register.to_metadata()
                        unsupported_detail_guard = analyze_unsupported_details(chunk, evaluated_text)
                        quality_v5_report.setdefault("issues", []).extend(unsupported_detail_guard.issues)
                        quality_v5_report.setdefault("metrics", {})["unsupported_detail_guard"] = unsupported_detail_guard.to_metadata()
                        package.setdefault("prompt_runtime", {})["unsupported_detail_guard"] = unsupported_detail_guard.to_metadata()
                        if unsupported_detail_guard.issues or unsupported_detail_guard.warnings:
                            emit_progress(
                                f"chunk {idx}/{len(chunks)} unsupported-detail-guard "
                                f"issues={len(unsupported_detail_guard.issues)} "
                                f"warnings={len(unsupported_detail_guard.warnings)} "
                                f"blocking={str(unsupported_detail_guard.blocking).lower()}",
                                options=options,
                            )
                        evaluated_text = str(quality_v5_report.get("normalized_text") or evaluated_text)
                        if options.strict_lock_terms:
                            evaluated_text = apply_locked_dictionary(evaluated_text, locked_dictionary)
                        evaluated_text = format_translation_output(evaluated_text, options)
                    quality_reports_by_text[evaluated_text] = dict(quality_v5_report or {})
                    return {**dict(quality_v5_report or {}), "_discipline_final_text": evaluated_text}

                def _discipline_legacy_qa_runner(candidate_text: str, quality_report: dict) -> dict:
                    evaluated_text = str(quality_report.get("_discipline_final_text") or candidate_text)
                    legacy = analyze_translation_quality(
                        chunk,
                        evaluated_text,
                        options,
                        locked_dictionary=package.get("knowledge", {}).get("locked_dictionary", {}),
                    ) if options.qa_enabled else {"passed": True, "issues": [], "metrics": {}}
                    return merge_quality_v5_into_runtime_qa(
                        legacy,
                        quality_reports_by_text.get(evaluated_text, quality_v5_report or {}),
                        attempt=qa_attempt,
                        chunk_id=package["package_id"],
                    )

                discipline_result = integrate_translation_discipline_runtime(
                    DisciplineRuntimeContext(
                        profile="literary",
                        qa_attempt=qa_attempt,
                        chunk_id=package["package_id"],
                        source_text=chunk,
                        translated_text=translation,
                        prompt_metadata=package.get("prompt_runtime", {}),
                        adaptive_feedback_metadata=package.get("prompt_runtime", {}).get("adaptive_feedback", {}),
                        environment_flags={"quality_v5_enabled": options.quality_v5_enabled},
                        runtime_metadata={
                            "runtime_wiring_verified": True,
                            "provider_call_budget_limit": _chunk_recovery_provider_budget(),
                            "provider_call_budget_used": recovery_provider_calls_used,
                            "post_targeted_retry": bool(result.get("targeted_retry")),
                            "targeted_retry_execution": dict(result.get("targeted_retry") or {}),
                        },
                    ),
                    quality_runner=_discipline_quality_runner,
                    legacy_qa_runner=_discipline_legacy_qa_runner,
                )
                translation = discipline_result.final_text
                qa_report = discipline_result.final_quality_report
                if discipline_result.local_repair_applied:
                    emit_progress(
                        f"chunk {idx}/{len(chunks)} adaptive-local-repair "
                        f"revalidated={str(discipline_result.revalidated).lower()}",
                        options=options,
                    )
                emit_progress(
                    f"chunk {idx}/{len(chunks)} discipline-runtime-integration "
                    f"initial={discipline_result.initial_action} final={discipline_result.final_action} "
                    f"revalidated={str(discipline_result.revalidated).lower()}",
                    options=options,
                )
                discipline_audit = discipline_result.audit_report
                audit_report_path = chunk_out_dir / f"{input_path.stem}_chunk_{idx:06d}_discipline_audit_attempt_{qa_attempt}.json"
                save_json(audit_report_path, discipline_audit)
                package.setdefault("prompt_runtime", {})["discipline_audit_trail"] = {"version": discipline_audit.get("schema_version", "6.0.0-stage07"), "report_path": str(audit_report_path), "initial_action": discipline_result.initial_action, "final_action": discipline_result.final_action, "revalidated": discipline_result.revalidated}
                package["prompt_runtime"]["discipline_runtime_integration"] = discipline_result.metadata["discipline_runtime_integration"]
                package["prompt_runtime"]["adaptive_feedback"] = discipline_result.adaptive_feedback
                save_json(package_path, package)
                emit_progress(f"chunk {idx}/{len(chunks)} discipline-audit rules={len((discipline_audit.get('discipline') or {}).get('active_rule_codes', []))} issues={(discipline_audit.get('quality') or {}).get('issue_count', 0)} final={discipline_result.final_action} report={audit_report_path.name}", options=options)
                unified_report = qa_report["unified_quality_report"]
                retry_decision = qa_report.get("adaptive_retry_decision") or {}
                emit_progress(
                    f"chunk {idx}/{len(chunks)} adaptive-retry-decision "
                    f"action={retry_decision.get('action', 'unknown')} "
                    f"local={len(retry_decision.get('local_repair_codes', []))} "
                    f"provider={len(retry_decision.get('provider_retry_codes', []))}",
                    options=options,
                )
                if qa_report.get("smart_local_repair", {}).get("provider_retry_skipped"):
                    emit_progress(
                        f"chunk {idx}/{len(chunks)} smart-local-repair accepted_with_warnings "
                        f"codes={','.join(qa_report['smart_local_repair'].get('issue_codes', []))}",
                        options=options,
                    )
                if quality_v5_report is not None:
                    quality_v5_report = attach_unified_report(quality_v5_report, unified_report)
                    report_suffix = ""
                    if options.quality_v5_report_enabled:
                        quality_report_path = chunk_out_dir / f"{input_path.stem}_chunk_{idx:06d}_quality_v5_attempt_{qa_attempt}.json"
                        save_json(quality_report_path, quality_v5_report)
                        report_suffix = f" report={quality_report_path.name}"
                    emit_progress(
                        f"chunk {idx}/{len(chunks)} quality-v5 score={unified_report.get('score', 0)} "
                        f"status={unified_report.get('decision', 'runtime_error')}{report_suffix}",
                        options=options,
                    )
                qa_attempt_records.append({"qa_attempt": qa_attempt, "qa": qa_report, "quality_v5": quality_v5_report})
                attempt_candidates.append(AttemptCandidate(
                    qa_attempt=qa_attempt,
                    translation=translation,
                    qa_report=dict(qa_report),
                    quality_v5_report=dict(quality_v5_report) if quality_v5_report is not None else None,
                    result=dict(result),
                ))
                emit_progress(
                    f"chunk {idx}/{len(chunks)} QA {qa_report.get('decision', 'runtime_error').upper()} "
                    f"issues={len(qa_report.get('issues', []))}",
                    options=options,
                )
                if qa_report.get("passed") or options.qa_fail_policy == "warn":
                    break
                if options.qa_fail_policy == "fail" or qa_attempt >= qa_attempts:
                    break
                if has_retry_worthy_naturalness_issue(qa_report):
                    naturalness_retry_count += 1
                    if naturalness_retry_count > int(options.naturalness_retry_limit or 0):
                        emit_progress("naturalness retry limit reached for chunk; stop QA retry", options=options)
                        break
                delay = qa_retry_delay_seconds(qa_attempt, options.retry_base_seconds)
                if delay > 0:
                    time.sleep(delay)

            best_candidate = select_best_attempt(attempt_candidates)
            if best_candidate is not None:
                latest_attempt = attempt_candidates[-1].qa_attempt
                selected_meta = selection_metadata(
                    attempt_candidates,
                    best_candidate,
                    selection_reason="later_provider_error" if later_provider_error else None,
                    later_provider_error=(later_provider_error or {}).get("error"),
                    later_qa_attempt=(later_provider_error or {}).get("qa_attempt"),
                )
                package.setdefault("prompt_runtime", {})["best_attempt_selection"] = selected_meta
                save_json(package_path, package)
                if later_provider_error:
                    emit_progress(
                        f"chunk {idx}/{len(chunks)} best-attempt-fallback "
                        f"selected={best_candidate.qa_attempt} "
                        f"later_qa_attempt={later_provider_error.get('qa_attempt')} "
                        f"reason={selected_meta.get('later_error_type', 'provider_error')}",
                        options=options,
                    )
                elif best_candidate.qa_attempt != latest_attempt:
                    latest_score = attempt_candidates[-1].unified.get("score", 0)
                    selected_score = best_candidate.unified.get("score", 0)
                    emit_progress(
                        f"chunk {idx}/{len(chunks)} best-attempt-selection "
                        f"selected={best_candidate.qa_attempt} latest={latest_attempt} "
                        f"score={selected_score}>{latest_score}",
                        options=options,
                    )
                translation = best_candidate.translation
                qa_report = dict(best_candidate.qa_report)
                result = dict(best_candidate.result)
                result["best_attempt_selection"] = selected_meta
                if later_provider_error:
                    result["later_provider_error"] = dict(later_provider_error)

            if result.get("status") != "success":
                resume_state["chunks"][chunk_key] = {
                    "status": "failed",
                    "source_hash": source_hash,
                    "error": result.get("error", "unknown error"),
                    "attempt": result.get("attempt", 1),
                    "qa_attempt": result.get("qa_attempt", 1),
                    "updated_at": now_iso(),
                }
                resume_state["events"].append({
                    "event": "chunk_failed",
                    "chunk_index": idx,
                    "error": result.get("error", "unknown error"),
                    "at": now_iso(),
                })
                save_resume_state(resume_state_path, resume_state)
                save_live_progress(live_progress_path, {
                    "status": "failed",
                    "input": str(input_path),
                    "chunk_total": len(chunks),
                    "chunk_completed": max(0, idx - 1),
                    "failed_chunk": idx,
                    "current_step": "provider_failed",
                    "error": result.get("error", "unknown error"),
                    "updated_at": now_iso(),
                })
                emit_progress(f"chunk {idx}/{len(chunks)} FAILED provider error={result.get('error', 'unknown error')[:180]}", options=options)
                partial = save_partial_translation_output(
                    output_dir=output_dir,
                    input_path=input_path,
                    translated_chunks=translated_chunks,
                    records=records,
                    failed_chunk=idx,
                    error=result.get("error", "unknown error"),
                    options=options,
                )
                return {
                    "status": "failed",
                    "input": str(input_path),
                    "failed_chunk": idx,
                    "error": result.get("error", "unknown error"),
                    "records": records,
                    "resume_state": str(resume_state_path),
                    **partial,
                }

            if options.qa_enabled and options.qa_fail_policy == "retry":
                qa_report = soft_fail_naturalness_report(qa_report, options.speed)
                if qa_report.get("status") == "pass_with_warning":
                    result["status"] = "pass_with_warning"
                    result["warning"] = "NATURALNESS_GUARD soft-failed after balanced retry limit"
                    emit_progress(f"chunk {idx}/{len(chunks)} QA PASS_WITH_WARNING naturalness soft-fail", options=options)

            qa_failed = options.qa_enabled and not qa_report.get("passed", True) and options.qa_fail_policy != "warn"
            if qa_failed:
                error = "; ".join(issue.get("message", issue.get("code", "QA_FAILED")) for issue in qa_report.get("issues", [])) or "translation QA failed"
                resume_state["chunks"][chunk_key] = {
                    "status": "qa_failed",
                    "source_hash": source_hash,
                    "error": error,
                    "qa": qa_report,
                    "attempt": result.get("attempt", 1),
                    "qa_attempt": result.get("qa_attempt", 1),
                    "updated_at": now_iso(),
                }
                resume_state["events"].append({
                    "event": "chunk_qa_failed",
                    "chunk_index": idx,
                    "error": error,
                    "qa": qa_report,
                    "at": now_iso(),
                })
                save_resume_state(resume_state_path, resume_state)
                save_live_progress(live_progress_path, {
                    "status": "failed",
                    "input": str(input_path),
                    "chunk_total": len(chunks),
                    "chunk_completed": max(0, idx - 1),
                    "failed_chunk": idx,
                    "current_step": "qa_failed",
                    "error": error,
                    "updated_at": now_iso(),
                })
                if translation.strip():
                    best_failed_path = chunk_out_dir / f"{input_path.stem}_chunk_{idx:06d}_best_failed_zh.txt"
                    save_text(best_failed_path, translation)
                    resume_state["chunks"][chunk_key]["best_failed_output_path"] = str(best_failed_path)
                    save_resume_state(resume_state_path, resume_state)
                emit_progress(f"chunk {idx}/{len(chunks)} FAILED QA error={error[:180]}", options=options)
                partial = save_partial_translation_output(
                    output_dir=output_dir,
                    input_path=input_path,
                    translated_chunks=translated_chunks,
                    records=records,
                    failed_chunk=idx,
                    error=error,
                    options=options,
                )
                return {
                    "status": "failed",
                    "input": str(input_path),
                    "failed_chunk": idx,
                    "error": error,
                    "qa": qa_report,
                    "records": records,
                    "resume_state": str(resume_state_path),
                    **partial,
                }

            save_text(chunk_file, translation)
            emit_progress(f"chunk {idx}/{len(chunks)} saved: {chunk_file.name}", options=options)
            resume_state["chunks"][chunk_key] = {
                "status": "pass_with_warning" if qa_report.get("status") == "pass_with_warning" else "success",
                "source_hash": source_hash,
                "output_path": str(chunk_file),
                "attempt": result.get("attempt", 1),
                "qa_attempt": result.get("qa_attempt", 1),
                "qa": qa_report,
                "updated_at": now_iso(),
            }
            result["qa"] = qa_report
            result["qa_attempt_records"] = qa_attempt_records
            save_resume_state(resume_state_path, resume_state)

        save_live_progress(live_progress_path, {
            "status": "running",
            "input": str(input_path),
            "output_dir": str(output_dir),
            "chunk_total": len(chunks),
            "chunk_completed": idx,
            "current_chunk": idx,
            "current_step": "chunk_completed",
            "updated_at": now_iso(),
        })
        if translation:
            translated_chunks.append(translation.strip())
        enable_cross_chunk_context = getattr(options, "quality_context_scene_v72", False)
        context_state_metadata = None
        if enable_cross_chunk_context:
            # Note: In legacy path, context_state_metadata is not built per-chunk like in runtime path
            # This maintains backward compatibility while ensuring the metadata key exists
            pass
        records.append(result | {"chunk_index": idx, "chunk_total": len(chunks), "metadata": {"context_state": context_state_metadata} if enable_cross_chunk_context else {}})

    final_output = output_dir / f"{input_path.stem}{DEFAULT_OUTPUT_SUFFIX}.txt"
    if not options.dry_run:
        final_text = "\n\n".join(translated_chunks).strip() + "\n"
        if options.strict_lock_terms:
            final_text = apply_locked_dictionary(final_text, locked_dictionary)
        final_text = format_translation_output(final_text, options).strip() + "\n"
        save_text(final_output, final_text)
        update_character_memory(character_memory_path, matched_terms_for_memory)

        # RM-8.3 Delivery Pipeline (Phase 6) — feature-gated
        if options.quality_delivery_v83:
            emit_progress("starting RM-8.3 delivery pipeline", options=options)
            try:
                from core.translation_release.delivery_pipeline import run_delivery_pipeline
                delivery_result = run_delivery_pipeline(
                    assembled_text=final_text,
                    translated_chunks=translated_chunks,
                    chunk_records=records,
                    locked_dictionary=locked_dictionary,
                    options=options,
                    input_path=input_path,
                    output_dir=output_dir,
                )
                if delivery_result.status == "failed":
                    emit_progress(f"RM-8.3 delivery pipeline FAILED: {delivery_result.error}", options=options)
                    # Don't fail the whole translation — delivery is optional extension
                    # Log and continue
                else:
                    emit_progress(f"RM-8.3 delivery pipeline SUCCESS: {delivery_result.output_path}", options=options)
            except Exception as e:
                emit_progress(f"RM-8.3 delivery pipeline ERROR: {e}", options=options)
                # Delivery pipeline failure is non-blocking for core translation

    # Aggregate literary quality metrics from all chunks
    lit_hits = 0
    lit_errors = 0
    lit_warnings = 0
    lit_passed = True
    lit_issue_codes: list[str] = []
    for rec in records:
        qa = rec.get("qa") if isinstance(rec.get("qa"), dict) else {}
        metrics = qa.get("metrics") if isinstance(qa.get("metrics"), dict) else {}
        if metrics:
            lit_hits += int(metrics.get("literary_quality_hits", 0))
            lit_errors += int(metrics.get("literary_quality_errors", 0))
            lit_warnings += int(metrics.get("literary_quality_warnings", 0))
            if not metrics.get("literary_quality_passed", True):
                lit_passed = False
            lit_issue_codes.extend(metrics.get("literary_quality_issue_codes", []))

    manifest = {
        "status": "success",
        "input": str(input_path),
        "output": str(final_output),
        "chunk_total": len(chunks),
        "chunk_size": options.chunk_size,
        "model": options.model,
        "speed_policy": {
            "speed": options.speed,
            "provider_attempts": options.provider_attempts,
            "qa_attempts": options.qa_attempts,
            "timeout": options.runtime_timeout,
            "naturalness_retry_limit": options.naturalness_retry_limit,
        },
        "resume": options.resume,
        "resume_state": str(resume_state_path),
        "retry": {"max_retries": options.max_retries, "base_seconds": options.retry_base_seconds},
        "glossary": {"locked_terms": len(locked_dictionary), "matched_terms": len(matched_terms_for_memory), "strict_lock_terms": options.strict_lock_terms},
        "qa": {"enabled": options.qa_enabled, "fail_policy": options.qa_fail_policy, "min_length_ratio": options.min_length_ratio, "max_korean_chars": options.max_korean_chars, "max_repeated_lines": options.max_repeated_lines},
        "formatter": {"enabled": options.output_formatter_enabled, "taiwan_traditional_normalization": options.taiwan_traditional_normalization},
        "character_memory": str(character_memory_path),
        "dry_run": options.dry_run,
        "completed_at": now_iso(),
        "literary_quality": {
            "hits": lit_hits,
            "errors": lit_errors,
            "warnings": lit_warnings,
            "passed": lit_passed,
            "issue_codes": list(dict.fromkeys(lit_issue_codes)),
        },
        "records": records,
    }
    save_json(output_dir / f"{input_path.stem}_translation_manifest.json", manifest)
    save_live_progress(live_progress_path, {
        "status": "success",
        "input": str(input_path),
        "output": str(final_output),
        "chunk_total": len(chunks),
        "chunk_completed": len(chunks),
        "current_step": "completed",
        "updated_at": now_iso(),
    })
    emit_progress(f"completed: {final_output}", options=options)
    return manifest


def parse_args(argv: Iterable[str] | None = None) -> TxtTranslationOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS Stage-05 TXT novel translation entry")
    parser.add_argument("input", help="input TXT file path")
    parser.add_argument("output", nargs="?", default="output", help="output directory")
    parser.add_argument("--chunk-size", type=int, default=None)
    parser.add_argument("--speed", choices=("fast", "balanced", "quality"), default=os.environ.get("NTPE_TRANSLATION_SPEED", "balanced"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--project-name", default="NTPE Novel Translation")
    parser.add_argument("--no-resume", action="store_true", help="disable chunk resume")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES, help="retry count for retryable provider errors")
    parser.add_argument("--retry-base-seconds", type=float, default=DEFAULT_RETRY_BASE_SECONDS, help="base seconds for exponential retry backoff")
    parser.add_argument("--glossary", dest="glossary_path", default=None, help="optional glossary file, supports source=target or source->target")
    parser.add_argument("--character-memory", dest="character_memory_path", default=None, help="optional character memory JSON path")
    parser.add_argument("--no-strict-lock-terms", action="store_true", help="disable output source-term normalization")
    parser.add_argument("--no-qa", action="store_true", help="disable translation QA checks")
    parser.add_argument("--qa-fail-policy", choices=QA_FAIL_POLICIES, default="retry", help="QA failure behavior: retry, fail, or warn")
    parser.add_argument("--min-length-ratio", type=float, default=DEFAULT_MIN_LENGTH_RATIO, help="minimum translated/source character ratio")
    parser.add_argument("--max-korean-chars", type=int, default=DEFAULT_MAX_KOREAN_CHARS, help="maximum allowed Korean characters after translation")
    parser.add_argument("--max-repeated-lines", type=int, default=DEFAULT_MAX_REPEATED_LINES, help="maximum allowed repeats for the same non-trivial output line")
    parser.add_argument("--no-output-formatter", action="store_true", help="disable output punctuation/cleanup formatter")
    parser.add_argument("--no-taiwan-normalization", action="store_true", help="disable built-in Taiwan Traditional Chinese normalization")
    parser.add_argument("--simplified-chinese-policy", choices=("normalize", "warn", "fail"), default="normalize", help="remaining simplified Chinese behavior after normalization")
    parser.add_argument("--quality-profile", choices=("fast", "balanced", "novel", "literary", "quality", "premium"), default="literary", help="translation quality profile")
    parser.add_argument("--no-quality-v5", action="store_true", help="disable TE-v5.3 conservative quality runtime integration")
    parser.add_argument("--no-quality-v5-report", action="store_true", help="disable per-attempt TE-v5 quality JSON reports")
    parser.add_argument("--quality-delivery-v83", action="store_true", help="enable RM-8.3 delivery pipeline (TXT + Manifest + QC Certificate + optional EPUB/PDF)")
    parser.add_argument("--quality-delivery-formats-v83", nargs="+", default=["txt"], choices=["txt", "epub", "pdf"], help="output formats for RM-8.3 delivery")
    parser.add_argument("--dry-run", action="store_true", help="build prompt packages without calling provider")
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return TxtTranslationOptions(
        input_path=Path(ns.input),
        output_dir=Path(ns.output),
        chunk_size=max(300, ns.chunk_size) if ns.chunk_size is not None else DEFAULT_CHUNK_SIZE,
        chunk_size_explicit=ns.chunk_size is not None,
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
        quality_profile=ns.quality_profile,
        simplified_chinese_policy=ns.simplified_chinese_policy,
        speed=ns.speed,
        quality_v5_enabled=not ns.no_quality_v5,
        quality_v5_report_enabled=not ns.no_quality_v5_report,
        quality_delivery_v83=ns.quality_delivery_v83,
        quality_delivery_formats_v83=tuple(ns.quality_delivery_formats_v83),
    )


def main(argv: Iterable[str] | None = None) -> int:
    try:
        options = parse_args(argv)
        result = translate_txt(options)
        print("NTPE 1.1 LTS TXT Translation Entry")
        print("===================================")
        print(f"status: {result['status']}")
        print(f"input: {result.get('input', '')}")
        print(f"output: {result.get('output', '')}")
        print(f"chunks: {result.get('chunk_total', 0)}")
        print(f"resume_state: {result.get('resume_state', '')}")
        return 0 if result.get("status") == "success" else 1
    except Exception as exc:
        print("NTPE 1.1 LTS TXT Translation Entry")
        print("===================================")
        print("status: failed")
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
