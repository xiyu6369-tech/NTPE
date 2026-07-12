from __future__ import annotations

from core.adaptive_context import calculate_dynamic_budget

from .model import ProfileBudgetDecision, ProfileBudgetRequest

PROFILE_BUDGET_VERSION = "7.0.0-stage08.2"
PROFILE_CONTEXT_CAPS = {
    "fast": 64,
    "balanced": 96,
    "novel": 160,
    "literary": 192,
    "quality": 224,
    "premium": 256,
}


def evaluate_profile_budget(request: ProfileBudgetRequest) -> ProfileBudgetDecision:
    profile = str(request.profile or "").strip().lower()
    blockers: list[str] = []
    limitations: list[str] = []
    cap = PROFILE_CONTEXT_CAPS.get(profile, 0)
    if not cap:
        blockers.append("profile-not-supported")

    dynamic = calculate_dynamic_budget(
        model_context_limit=request.model_context_limit,
        fixed_prompt_tokens=request.fixed_prompt_tokens,
        source_tokens=request.source_tokens,
        reserved_output_tokens=request.reserved_output_tokens,
        requested_context_tokens=None,
    )
    requested = cap if request.requested_context_tokens is None else max(0, int(request.requested_context_tokens))
    if requested <= 0:
        blockers.append("positive-context-budget-required")
    if dynamic.hard_limit <= 0:
        blockers.append("no-context-capacity")
    if requested > cap and cap:
        limitations.append("requested-budget-clamped-to-profile-cap")
    if cap > dynamic.hard_limit and dynamic.hard_limit > 0:
        limitations.append("profile-cap-clamped-to-hard-limit")

    effective = min(cap, requested, dynamic.hard_limit) if not blockers else 0
    if effective <= 0 and not blockers:
        blockers.append("effective-context-budget-empty")
    blockers = list(dict.fromkeys(blockers))
    limitations = list(dict.fromkeys(limitations))
    ready = not blockers
    return ProfileBudgetDecision(
        version=PROFILE_BUDGET_VERSION,
        status="pass" if ready else "fail",
        ready=ready,
        profile=profile,
        profile_cap_tokens=cap,
        hard_limit_tokens=dynamic.hard_limit,
        requested_context_tokens=requested,
        effective_context_tokens=effective,
        blockers=tuple(blockers),
        limitations=tuple(limitations),
        metadata={
            "content_redacted": True,
            "deterministic": True,
            "default_runtime_activation": False,
            "runtime_auto_hook": False,
            "provider_policy_modified": False,
            "prompt_policy_modified": False,
            "quality_gate_modified": False,
            "profile_caps": dict(PROFILE_CONTEXT_CAPS),
            "translation_quality_improvement_claimed": False,
            "provider_latency_improvement_claimed": False,
        },
    )
