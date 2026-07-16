from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Callable, Mapping

from core.lcr_production_shadow import create_shadow_input, deterministic_fingerprint, run_lcr_production_shadow

from .bounded_execution import SHADOW_EXECUTOR
from .evidence_sink import DisabledEvidenceSink
from .feature_flags import GLOBAL_FLAG, KILL_SWITCH, minimal_shadow_flags, resolve_hook_flags
from .models import HOOK_SYMBOL, HOOK_VERSION, HookEvidence, HookOutcome


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
    clock_ns: Callable[[], int],
    created_at_factory: Callable[[], str] | None,
) -> HookOutcome:
    started = clock_ns()
    try:
        before = _canonical_hash(production_metadata)
        metadata = _extract_metadata(production_metadata)
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
        after = _canonical_hash(production_metadata)
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
            modules_evaluated=result.modules_evaluated,
            provider_requests_executed=result.provider_requests_executed,
            production_output_changed=result.production_output_changed,
            baseline_changed=before != after or result.baseline_changed,
            warnings=tuple(warnings),
            blocking_reasons=result.blocking_reasons,
            result_discarded=False,
            duration_ms=round(duration_ms, 6),
            created_at=created_at,
        )
        return HookOutcome(
            status, True, evidence, before, after,
            prompt_hash, str(_extract_metadata(production_metadata)["prompt_identity"]),
            provider_identity, _canonical_hash({"provider": metadata["provider_identity"], "model": metadata["model_identity"]}),
            resume_hash, str(_extract_metadata(production_metadata)["resume_identity"]),
            output_hash, str(_extract_metadata(production_metadata)["output_contract_identity"]),
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

    caller_started = time.perf_counter_ns()
    submission = SHADOW_EXECUTOR.submit(
        lambda: _compute_shadow_outcome(
            production_metadata, clock_ns=clock_ns, created_at_factory=created_at_factory,
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
