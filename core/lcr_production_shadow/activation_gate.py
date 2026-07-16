from __future__ import annotations

from typing import Mapping

from .models import ActivationGateResult


REQUIRED = (
    "batch9_ready", "all_lcr_regressions_pass", "production_boundary_unchanged",
    "shadow_deterministic", "shadow_exceptions_isolated", "provider_requests_zero",
    "prompt_budget_within_limit", "request_cost_within_policy", "kill_switch_verified",
    "rollback_verified", "security_scan_pass", "manual_approval_present",
)


def evaluate_activation_gate(evidence: Mapping[str, bool]) -> ActivationGateResult:
    requirements = {name: evidence.get(name) is True for name in REQUIRED}
    missing = tuple(name for name, passed in requirements.items() if not passed)
    if not evidence or any(name not in evidence for name in REQUIRED):
        status = "insufficient_evidence"
    else:
        status = "ready_for_shadow_hook" if not missing else "not_ready"
    return ActivationGateResult(status, requirements, missing, active_production_authorized=False)
