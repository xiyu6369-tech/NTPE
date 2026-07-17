from __future__ import annotations

from typing import Mapping

from .models import ExtendedShadowGate


REQUIREMENTS = (
    "single_hook_only",
    "hook_default_disabled",
    "kill_switch_default_enabled",
    "baseline_hash_unchanged",
    "prompt_identity_unchanged",
    "provider_identity_unchanged",
    "resume_unchanged",
    "output_unchanged",
    "provider_requests_zero",
    "network_requests_zero",
    "hook_exceptions_isolated",
    "timeout_budget_pass",
    "blocking_runner_test_passed",
    "caller_deadline_enforced",
    "late_result_discarded",
    "worker_count_bounded",
    "queue_bounded",
    "production_files_within_limit",
    "security_pass",
    "all_regressions_pass",
    "manual_approval_present",
)

CHARACTER_MEMORY_REQUIREMENTS = (
    "single_production_hook_unchanged",
    "character_memory_flag_default_false",
    "kill_switch_default_true",
    "immutable_snapshot_verified",
    "selection_read_only",
    "store_hash_unchanged",
    "prompt_identity_unchanged",
    "provider_identity_unchanged",
    "resume_unchanged",
    "output_unchanged",
    "memory_injected_false",
    "provider_requests_zero",
    "network_requests_zero",
    "bounded_deadline_pass",
    "late_results_discarded",
    "worker_count_bounded",
    "queue_bounded",
    "security_pass",
    "all_regressions_pass",
    "manual_approval_present",
)

CONTEXT_SCENE_REQUIREMENTS = (
    "single_production_hook_unchanged", "production_wrapper_unchanged",
    "context_scene_flag_default_false", "kill_switch_default_true",
    "immutable_snapshot_verified", "context_store_unchanged", "character_store_unchanged",
    "prompt_identity_unchanged", "provider_identity_unchanged", "resume_unchanged", "output_unchanged",
    "context_injected_false", "previous_translation_injected_false", "scene_state_applied_false",
    "cache_identity_applied_false", "provider_requests_zero", "network_requests_zero",
    "deadline_isolation_pass", "late_result_writes_zero", "worker_bounded", "queue_bounded",
    "security_pass", "all_regressions_pass", "manual_approval_present",
)


def evaluate_extended_shadow_gate(evidence: Mapping[str, object]) -> ExtendedShadowGate:
    if not isinstance(evidence, Mapping):
        return ExtendedShadowGate("invalid", {}, ("invalid_evidence",))
    requirements = {name: evidence.get(name) is True for name in REQUIREMENTS}
    missing_keys = tuple(name for name in REQUIREMENTS if name not in evidence)
    reasons = tuple(name for name, passed in requirements.items() if not passed)
    if missing_keys:
        status = "insufficient_evidence"
    else:
        status = "ready_for_extended_shadow" if not reasons else "not_ready"
    return ExtendedShadowGate(status, requirements, reasons, active_production_authorized=False)


def evaluate_character_memory_shadow_gate(evidence: Mapping[str, object]) -> ExtendedShadowGate:
    if not isinstance(evidence, Mapping):
        return ExtendedShadowGate("invalid", {}, ("invalid_evidence",))
    requirements = {name: evidence.get(name) is True for name in CHARACTER_MEMORY_REQUIREMENTS}
    missing_keys = tuple(name for name in CHARACTER_MEMORY_REQUIREMENTS if name not in evidence)
    reasons = tuple(name for name, passed in requirements.items() if not passed)
    if missing_keys:
        status = "insufficient_evidence"
    else:
        status = "ready_for_context_scene_shadow" if not reasons else "not_ready"
    return ExtendedShadowGate(status, requirements, reasons, active_production_authorized=False)


def evaluate_context_scene_shadow_gate(evidence: Mapping[str, object]) -> ExtendedShadowGate:
    if not isinstance(evidence, Mapping):
        return ExtendedShadowGate("invalid", {}, ("invalid_evidence",))
    requirements = {name: evidence.get(name) is True for name in CONTEXT_SCENE_REQUIREMENTS}
    missing_keys = tuple(name for name in CONTEXT_SCENE_REQUIREMENTS if name not in evidence)
    reasons = tuple(name for name, passed in requirements.items() if not passed)
    if missing_keys:
        status = "insufficient_evidence"
    else:
        status = "ready_for_dual_pass_shadow" if not reasons else "not_ready"
    return ExtendedShadowGate(status, requirements, reasons, active_production_authorized=False)
