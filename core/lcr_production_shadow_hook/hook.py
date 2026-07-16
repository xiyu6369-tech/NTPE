from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Callable, Mapping, Sequence

from core.character_memory_v2 import MemoryStore

from core.lcr_production_shadow import create_shadow_input, deterministic_fingerprint, run_lcr_production_shadow

from .bounded_execution import SHADOW_EXECUTOR
from .character_memory_shadow import (
    DEFAULT_SHADOW_SELECTION_BUDGET,
    build_character_memory_shadow_input,
    empty_character_memory_result,
    evaluate_character_memory_shadow,
)
from .evidence_sink import DisabledEvidenceSink
from .feature_flags import CHARACTER_MEMORY_FLAG, GLOBAL_FLAG, KILL_SWITCH, minimal_shadow_flags, resolve_hook_flags
from .models import CharacterMemoryShadowInput, HOOK_SYMBOL, HOOK_VERSION, HookEvidence, HookOutcome


SOFT_BUDGET_MS = 10.0
HARD_BUDGET_MS = 25.0
CALLER_WAIT_BUDGET_MS = 20.0
PROFILE_IDENTITIES = {
    "ko": ("literary-ko-zh-hant", "1.0"),
    "ja": ("literary-ja-zh-hant", "1.0"),
    "en": ("literary-en-zh-hant", "1.0"),
}


class _FrozenDict(dict[str, bool]):
    def _immutable(self, *args: object, **kwargs: object) -> None:
        raise TypeError("frozen shadow mapping")

    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = _immutable

    def __deepcopy__(self, memo: dict[int, object]) -> "_FrozenDict":
        return self


def _canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _freeze(value: object) -> object:
    """Detach recursively from the caller before work can outlive its deadline."""
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    return str(value)


def _extract_metadata(package: Mapping[str, object]) -> Mapping[str, object]:
    project = _mapping(package.get("project"))
    session = _mapping(package.get("session"))
    source = _mapping(package.get("source"))
    prompt = _mapping(package.get("prompt"))
    model = _mapping(package.get("model_profile"))
    runtime = _mapping(package.get("runtime"))
    context = _mapping(package.get("context"))
    knowledge = _mapping(package.get("knowledge"))
    document_seed = str(session.get("session_id") or package.get("package_id") or "unknown-document")
    values = {
        "document_id": "doc-" + hashlib.sha256(document_seed.encode("utf-8")).hexdigest()[:24],
        "chunk_index": int(session.get("chunk_index", 0) or 0),
        "source_hash": str(source.get("source_hash") or _canonical_hash(source)),
        "source_language": str(project.get("source_language") or "unknown"),
        "target_language": str(project.get("target_language") or "unknown"),
        "prompt_identity": _canonical_hash(prompt),
        "provider_identity": str(model.get("engine") or "baseline-provider"),
        "model_identity": str(model.get("model") or "baseline-model"),
        "quality_policy_identity": _canonical_hash(_mapping(package.get("qa_requirements"))),
        "resume_identity": _canonical_hash({"resume_key": session.get("resume_key", "")}),
        "output_contract_identity": _canonical_hash({"encoding": "utf-8", "format": "text"}),
        "baseline_context_fingerprint": _canonical_hash(context),
        "baseline_glossary_fingerprint": _canonical_hash(knowledge),
        "runtime_version": str(runtime.get("version") or HOOK_VERSION),
    }
    return MappingProxyType(values)


def _minimal_overrides(metadata: Mapping[str, object]) -> dict[str, Callable[[object], Mapping[str, object]]]:
    language = str(metadata["source_language"]).lower()
    selected = PROFILE_IDENTITIES.get(language)
    profile = {
        "selected_profile_id": selected[0] if selected else "",
        "selected_profile_version": selected[1] if selected else "",
        "selected_profile_fingerprint": _canonical_hash(selected or ("blocked", language)),
        "applied": False,
        "blocked": selected is None,
    }
    cache = {
        "cache_identity_built": True,
        "cache_identity": _canonical_hash({
            "source_hash": metadata["source_hash"],
            "prompt_identity": metadata["prompt_identity"],
            "model_identity": metadata["model_identity"],
        }),
        "cache_hit_applied": False,
        "provider_skipped": False,
        "applied": False,
    }
    route = {
        "prepare_only": True,
        "executed": False,
        "network_requests": 0,
        "provider_executed": False,
        "provider_identity": metadata["provider_identity"],
        "model_identity": metadata["model_identity"],
        "applied": False,
    }
    return {
        "multilingual_profile": lambda _: profile,
        "chunk_cache": lambda _: cache,
        "provider_routing": lambda _: route,
    }


def _empty_outcome(status: str, before: str, prompt: str, provider: str, resume: str, output: str, warning: str = "") -> HookOutcome:
    return HookOutcome(
        status, True, None, before, before, prompt, prompt, provider, provider,
        resume, resume, output, output, (warning,) if warning else (),
    )


def _discarded_outcome(
    status: str,
    duration_ms: float,
    warning: str,
) -> HookOutcome:
    fingerprint = hashlib.sha256(("discarded:" + status).encode("utf-8")).hexdigest()
    evidence = HookEvidence(
        hook_id=HOOK_SYMBOL + "-" + fingerprint[:16],
        shadow_status=status,
        input_fingerprint=fingerprint,
        modules_evaluated=(),
        provider_requests_executed=0,
        production_output_changed=False,
        baseline_changed=False,
        warnings=(warning, "result_discarded"),
        blocking_reasons=(),
        result_discarded=True,
        duration_ms=round(duration_ms, 6),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    return HookOutcome(
        status, True, evidence, "", "", "", "", "", "", "", "", "", "",
        evidence.warnings, True,
    )


def _compute_shadow_outcome(
    production_metadata: Mapping[str, object],
    *,
    package_hash: str,
    character_snapshot: CharacterMemoryShadowInput | None,
    character_pre_status: str,
    clock_ns: Callable[[], int],
    created_at_factory: Callable[[], str] | None,
) -> HookOutcome:
    started = clock_ns()
    try:
        before = package_hash
        metadata = production_metadata
        prompt_hash = str(metadata["prompt_identity"])
        provider_identity = _canonical_hash({"provider": metadata["provider_identity"], "model": metadata["model_identity"]})
        resume_hash = str(metadata["resume_identity"])
        output_hash = str(metadata["output_contract_identity"])
    except Exception:
        fallback = hashlib.sha256(b"invalid-shadow-metadata").hexdigest()
        return _empty_outcome("invalid", fallback, fallback, fallback, fallback, fallback, "metadata_adapter_exception")
    try:
        item = create_shadow_input(
            **metadata,
            feature_flag_state=_FrozenDict(minimal_shadow_flags()),
            created_at="",
        )
        result = run_lcr_production_shadow(
            item,
            flags=minimal_shadow_flags(),
            module_overrides=_minimal_overrides(metadata),
        )
        character_result = None
        modules = result.modules_evaluated
        if character_pre_status:
            character_result = empty_character_memory_result(status=character_pre_status)
            modules = (*modules, "character_memory")
        elif character_snapshot is not None:
            character_result = evaluate_character_memory_shadow(
                character_snapshot, now=character_snapshot.created_at or None,
            )
            modules = (*modules, "character_memory")
        after = before
        duration_ms = max(0.0, (clock_ns() - started) / 1_000_000)
        warnings = list(result.warnings)
        status = result.readiness_result
        if duration_ms > SOFT_BUDGET_MS:
            status = "degraded"
            warnings.append("soft_timeout_budget_exceeded")
        if before != after:
            status = "invalid"
            warnings.append("baseline_mutation_detected")
        created_at = (created_at_factory or (lambda: datetime.now(timezone.utc).isoformat()))()
        evidence = HookEvidence(
            hook_id=HOOK_SYMBOL + "-" + result.input_fingerprint[:16],
            shadow_status=status,
            input_fingerprint=result.input_fingerprint,
            modules_evaluated=modules,
            provider_requests_executed=result.provider_requests_executed,
            production_output_changed=result.production_output_changed,
            baseline_changed=before != after or result.baseline_changed,
            warnings=tuple(warnings),
            blocking_reasons=result.blocking_reasons,
            result_discarded=False,
            duration_ms=round(duration_ms, 6),
            created_at=created_at,
            character_memory=character_result,
        )
        return HookOutcome(
            status, True, evidence, before, after,
            prompt_hash, str(metadata["prompt_identity"]),
            provider_identity, _canonical_hash({"provider": metadata["provider_identity"], "model": metadata["model_identity"]}),
            resume_hash, str(metadata["resume_identity"]),
            output_hash, str(metadata["output_contract_identity"]),
            tuple(warnings), False,
        )
    except Exception:
        return _empty_outcome("degraded", before, prompt_hash, provider_identity, resume_hash, output_hash, "shadow_exception")


def run_read_only_lcr_shadow_hook(
    production_metadata: Mapping[str, object],
    *,
    feature_flags: Mapping[str, object] | None = None,
    evidence_sink: object | None = None,
    clock_ns: Callable[[], int] = time.perf_counter_ns,
    created_at_factory: Callable[[], str] | None = None,
    character_memory_store: MemoryStore | None = None,
    character_ids: Sequence[str] | None = None,
    character_memory_snapshot_id: str | None = None,
    character_memory_scope: Mapping[str, str] | None = None,
    character_memory_token_budget: int = DEFAULT_SHADOW_SELECTION_BUDGET,
) -> HookOutcome:
    """Run the single metadata-only hook; every failure preserves baseline behavior."""
    try:
        flags = resolve_hook_flags(feature_flags)
    except Exception:
        return _empty_outcome("blocked", "", "", "", "", "", "flag_parser_exception")
    if flags[KILL_SWITCH]:
        return _empty_outcome("blocked", "", "", "", "", "", "kill_switch_active")
    if not flags[GLOBAL_FLAG]:
        return _empty_outcome("skipped", "", "", "", "", "")

    # Both snapshots are created on the caller thread. A timed-out worker never
    # retains the mutable Production package or Character Memory Store.
    try:
        package_hash = _canonical_hash(production_metadata)
        production_snapshot = _freeze(_extract_metadata(production_metadata))
        if not isinstance(production_snapshot, Mapping):
            raise TypeError("production metadata must be a mapping")
    except Exception:
        return _empty_outcome("invalid", "", "", "", "", "", "metadata_adapter_exception")
    character_snapshot = None
    character_pre_status = ""
    if flags[CHARACTER_MEMORY_FLAG]:
        if character_memory_store is None or character_memory_snapshot_id is None or character_ids is None:
            character_pre_status = "metadata_unavailable"
        else:
            try:
                metadata = production_snapshot
                character_snapshot = build_character_memory_shadow_input(
                    character_memory_store,
                    document_id=str(metadata["document_id"]), chunk_index=int(metadata["chunk_index"]),
                    source_language=str(metadata["source_language"]), target_language=str(metadata["target_language"]),
                    character_ids=character_ids, snapshot_id=character_memory_snapshot_id,
                    scope=character_memory_scope, token_budget=character_memory_token_budget,
                    created_at=(created_at_factory or (lambda: ""))(),
                )
            except Exception:
                character_pre_status = "invalid"

    caller_started = time.perf_counter_ns()
    submission = SHADOW_EXECUTOR.submit(
        lambda: _compute_shadow_outcome(
            production_snapshot, package_hash=package_hash, character_snapshot=character_snapshot,
            character_pre_status=character_pre_status,
            clock_ns=clock_ns, created_at_factory=created_at_factory,
        ),
        wait_ms=CALLER_WAIT_BUDGET_MS,
    )
    caller_duration_ms = (time.perf_counter_ns() - caller_started) / 1_000_000
    if submission.status == "timed_out":
        return _discarded_outcome(
            "timed_out", caller_duration_ms, "hard_timeout_budget_exceeded",
        )
    if submission.status == "busy" or submission.outcome is None:
        return _discarded_outcome(
            "degraded", caller_duration_ms, "shadow_worker_busy",
        )
    outcome = submission.outcome
    if outcome.evidence is None:
        return outcome
    try:
        (evidence_sink or DisabledEvidenceSink()).write(outcome.evidence)
    except Exception:
        return HookOutcome(
            "degraded", True, outcome.evidence, outcome.before_hash, outcome.after_hash,
            outcome.prompt_before_hash, outcome.prompt_after_hash,
            outcome.provider_identity_before, outcome.provider_identity_after,
            outcome.resume_before_hash, outcome.resume_after_hash,
            outcome.output_contract_before_hash, outcome.output_contract_after_hash,
            (*outcome.warning_codes, "evidence_sink_exception"), outcome.result_discarded,
        )
    return outcome
