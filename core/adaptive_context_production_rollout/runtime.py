from __future__ import annotations

import copy
import functools
import hashlib
import os
from dataclasses import replace
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from core.adaptive_context import ContextItem, build_adaptive_context, estimate_tokens
from core.adaptive_context_integration.utils import canonical_hash
from core.adaptive_context_prompt_anchor import (
    anchored_context_text,
    bind_prompt_context_anchor,
    replace_anchored_context,
    resolve_prompt_context_anchor,
)

from .audit import write_rollout_audit
from .eligibility import production_blockers
from .metrics import RolloutMetrics
from .model import ProductionEvidence, RolloutConfig, RolloutRecord
from .rollback import RollbackController
from .sampling import deterministic_rollout_sample

ROLLOUT_VERSION = "7.0.0-stage08.4"
KILL_SWITCH_ENV = "NTPE_TE_V7_ACE_PRODUCTION_KILL_SWITCH"
_ORIGINAL_ATTR = "_ntpe_te_v7_stage084_original_build_prompt_package"
_WRAPPED_ATTR = "_ntpe_te_v7_stage084_production_wrapped"


class _Session:
    def __init__(self, config: RolloutConfig, evidence: ProductionEvidence, metrics: RolloutMetrics, controller: RollbackController, audit_path: str | Path | None):
        self.config = config
        self.evidence = evidence
        self.metrics = metrics
        self.controller = controller
        self.audit_path = audit_path


_SESSION: ContextVar[_Session | None] = ContextVar("ntpe_ace_production_rollout", default=None)


def _sha(value: str) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def kill_switch_enabled(config: RolloutConfig) -> bool:
    value = str(os.environ.get(KILL_SWITCH_ENV, "")).strip().lower()
    return config.kill_switch or value in {"1", "true", "yes", "on", "enabled"}


def _record(
    package: dict[str, object], config: RolloutConfig, evidence: ProductionEvidence, *, decision: str,
    blockers: tuple[str, ...], bucket: int, activated: bool = False, fallback: bool = False,
    baseline: int = 0, ace: int = 0, changed: bool = False,
) -> RolloutRecord:
    source = package.get("source", {})
    source = source if isinstance(source, dict) else {}
    session = package.get("session", {})
    session = session if isinstance(session, dict) else {}
    return RolloutRecord(
        version=ROLLOUT_VERSION,
        package_id_sha256=_sha(str(package.get("package_id", ""))),
        source_hash_sha256=_sha(str(source.get("source_hash", ""))),
        chunk_index=int(session.get("chunk_index", 0) or 0),
        profile=config.profile,
        decision=decision,
        activated=activated,
        fallback_used=fallback,
        blockers=blockers,
        rollout_bucket=bucket,
        rollout_percent=config.rollout_percent,
        policy_version=config.policy_version,
        strategy_version=evidence.strategy_version,
        baseline_context_tokens=baseline,
        ace_context_tokens=ace,
        estimated_tokens_saved=max(0, baseline - ace) if activated else 0,
        payload_changed=changed,
        provider_calls_added=0,
        metadata={
            "content_redacted": True,
            "single_chunk_decision": True,
            "provider_settings_unchanged": True,
            "provider_timeout_is_not_admission_failure": True,
            "partial_merge": False,
        },
    )


def apply_production_rollout(
    package: dict[str, object], config: RolloutConfig, evidence: ProductionEvidence,
    *, metrics: RolloutMetrics | None = None, controller: RollbackController | None = None,
    audit_path: str | Path | None = None,
) -> RolloutRecord:
    metrics = metrics or RolloutMetrics()
    controller = controller or RollbackController()
    source = package.get("source", {})
    session = package.get("session", {})
    source = source if isinstance(source, dict) else {}
    session = session if isinstance(session, dict) else {}
    source_hash = str(source.get("source_hash", ""))
    chunk_index = int(session.get("chunk_index", 0) or 0)
    sample = deterministic_rollout_sample(source_hash, chunk_index, config.profile, config.policy_version, config.rollout_percent)
    dynamic_kill = kill_switch_enabled(config)
    blockers = list(production_blockers(config, evidence, kill_switch=dynamic_kill))
    if controller.disabled:
        blockers.append("automatic-rollback-active")
    if not source_hash or chunk_index <= 0:
        blockers.append("invalid-package-identity")
    if blockers:
        if dynamic_kill and not controller.disabled:
            controller.trigger("kill-switch-enabled")
        record = _record(package, config, evidence, decision="disabled", blockers=tuple(dict.fromkeys(blockers)), bucket=sample.bucket)
        metrics.observe(record); write_rollout_audit(record, audit_path); return record
    if not sample.sampled:
        record = _record(package, config, evidence, decision="not-sampled", blockers=(), bucket=sample.bucket)
        metrics.observe(record); write_rollout_audit(record, audit_path); return record

    if config.validation_mode == "shadow-compatible":
        candidate_package = copy.deepcopy(package)
        candidate = apply_production_rollout(
            candidate_package,
            replace(config, validation_mode="assembly-only"),
            evidence,
            metrics=RolloutMetrics(),
            controller=RollbackController(),
        )
        record = _record(
            package, config, evidence, decision="shadow-compatible", blockers=candidate.blockers,
            bucket=sample.bucket, fallback=candidate.fallback_used,
            baseline=candidate.baseline_context_tokens, ace=candidate.ace_context_tokens,
        )
        metrics.observe(record); write_rollout_audit(record, audit_path); return record

    original = copy.deepcopy(package)
    prompt_before = copy.deepcopy(package.get("prompt"))
    model_before = copy.deepcopy(package.get("model_profile"))
    bound = bind_prompt_context_anchor(package)
    anchor = resolve_prompt_context_anchor(package)
    original_context = anchored_context_text(package, anchor)
    baseline = estimate_tokens(original_context) if original_context else 0
    reasons: list[str] = []
    if not bound.addressable or not anchor.addressable or anchor.strategy != "package-bound":
        reasons.append(bound.reason or anchor.reason or "package-bound-anchor-invalid")
    if not original_context:
        reasons.append("package-bound-anchor-content-unavailable")
    candidate = ""
    candidate_tokens = baseline
    if not reasons:
        budget = min(evidence.effective_context_tokens, max(1, baseline - 1))
        item = ContextItem("previous_chunk_tail", "narrative", original_context, relevance=1.0, recency=1.0, continuity=1.0)
        result = build_adaptive_context((item,), model_context_limit=budget, reserved_output_tokens=0, requested_context_tokens=budget)
        if not result.admissible or result.fallback_required or len(result.selected) != 1:
            reasons.extend(result.fallback_reasons or ("ace-admission-failed",))
        else:
            candidate = result.selected[0].content
            candidate_tokens = result.selected[0].estimated_tokens
            if not candidate or candidate == original_context or candidate_tokens >= baseline:
                reasons.append("no-token-reduction")
    if not reasons and not replace_anchored_context(package, anchor, candidate):
        reasons.append("package-bound-anchor-replacement-failed")
    prompt_after = package.get("prompt")
    if not reasons:
        user_before = str(prompt_before.get("user_prompt", "")) if isinstance(prompt_before, dict) else ""
        user_after = str(prompt_after.get("user_prompt", "")) if isinstance(prompt_after, dict) else ""
        expected = user_before[:anchor.start] + candidate + user_before[anchor.end:]
        if user_after != expected:
            reasons.append("payload-anchor-mismatch")
        other_before = dict(prompt_before) if isinstance(prompt_before, dict) else {}
        other_after = dict(prompt_after) if isinstance(prompt_after, dict) else {}
        other_before.pop("user_prompt", None); other_after.pop("user_prompt", None)
        if other_before != other_after:
            reasons.append("prompt-outside-anchor-changed")
        if package.get("model_profile") != model_before:
            reasons.append("provider-settings-changed")
    if reasons:
        package.clear(); package.update(original)
        if any("anchor-mismatch" in reason or "outside-anchor" in reason or "provider-settings" in reason for reason in reasons):
            controller.trigger(*reasons)
        record = _record(package, config, evidence, decision="fallback", blockers=tuple(dict.fromkeys(reasons)), bucket=sample.bucket, fallback=True, baseline=baseline, ace=baseline)
        metrics.observe(record); write_rollout_audit(record, audit_path); return record
    changed = canonical_hash(package) != canonical_hash(original)
    if not changed:
        package.clear(); package.update(original)
        record = _record(package, config, evidence, decision="fallback", blockers=("payload-unchanged",), bucket=sample.bucket, fallback=True, baseline=baseline, ace=baseline)
    else:
        record = _record(package, config, evidence, decision="activated", blockers=(), bucket=sample.bucket, activated=True, baseline=baseline, ace=candidate_tokens, changed=True)
    metrics.observe(record); write_rollout_audit(record, audit_path); return record


@contextmanager
def production_rollout_session(
    config: RolloutConfig, evidence: ProductionEvidence, *, metrics: RolloutMetrics | None = None,
    controller: RollbackController | None = None, audit_path: str | Path | None = None,
) -> Iterator[tuple[RolloutMetrics, RollbackController]]:
    active_metrics = metrics or RolloutMetrics()
    active_controller = controller or RollbackController()
    token = _SESSION.set(_Session(config, evidence, active_metrics, active_controller, audit_path))
    try:
        yield active_metrics, active_controller
    finally:
        _SESSION.reset(token)


def install_production_rollout_hook() -> bool:
    import lts.txt_translation_runtime as runtime
    current = runtime.build_prompt_package
    if getattr(current, _WRAPPED_ATTR, False):
        return False
    original: Callable[..., dict[str, object]] = current

    @functools.wraps(original)
    def wrapped(*args: Any, **kwargs: Any) -> dict[str, object]:
        package = original(*args, **kwargs)
        active = _SESSION.get()
        if active is not None:
            session = package.get("session", {})
            session = session if isinstance(session, dict) else {}
            chunk_index = int(session.get("chunk_index", 0) or 0)
            if active.config.target_chunk and chunk_index > active.config.target_chunk:
                from core.adaptive_context_canary_validation.stop import target_complete_error
                raise target_complete_error(active.config.target_chunk)
            apply_production_rollout(package, active.config, active.evidence, metrics=active.metrics, controller=active.controller, audit_path=active.audit_path)
        return package

    setattr(wrapped, _WRAPPED_ATTR, True)
    setattr(runtime, _ORIGINAL_ATTR, original)
    runtime.build_prompt_package = wrapped
    return True
