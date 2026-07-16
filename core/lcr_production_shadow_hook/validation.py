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
