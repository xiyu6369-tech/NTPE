from __future__ import annotations

from .model import StrategySelectionDecision, StrategySelectionEvidence, StrategySelectionRequest

STRATEGY_SELECTION_VERSION = "7.0.0-stage08.3"
ELIGIBLE_PROFILES = ("literary", "novel")
ELIGIBLE_POLICY_MODE = "production_canary"
SELECTED_STRATEGY = "safe_extractive_production_canary"


def evaluate_strategy_selection(
    evidence: StrategySelectionEvidence,
    request: StrategySelectionRequest,
) -> StrategySelectionDecision:
    blockers: list[str] = []
    limitations: list[str] = []
    profile = str(request.profile or "").strip().lower()

    if request.kill_switch:
        blockers.append("kill-switch-enabled")
    if not request.explicitly_enabled:
        blockers.append("explicit-enable-required")
    if profile not in ELIGIBLE_PROFILES:
        blockers.append("profile-not-eligible")
    if not evidence.policy_ready or evidence.policy_status != "pass":
        blockers.append("activation-policy-not-ready")
    if evidence.policy_mode != ELIGIBLE_POLICY_MODE:
        blockers.append("activation-policy-mode-not-eligible")
    if not evidence.budget_ready or evidence.budget_status != "pass":
        blockers.append("profile-budget-not-ready")
    if evidence.policy_profile != profile or evidence.budget_profile != profile:
        blockers.append("profile-evidence-mismatch")
    if evidence.rollout_percent <= 0 or evidence.rollout_percent > 5:
        blockers.append("rollout-percent-outside-stage-limit")
    if evidence.effective_context_tokens <= 0:
        blockers.append("positive-effective-budget-required")
    if evidence.effective_context_tokens > evidence.profile_cap_tokens:
        blockers.append("effective-budget-exceeds-profile-cap")
    if evidence.effective_context_tokens > evidence.hard_limit_tokens:
        blockers.append("effective-budget-exceeds-hard-limit")

    blockers = list(dict.fromkeys(blockers))
    ready = not blockers
    if ready and evidence.effective_context_tokens == evidence.profile_cap_tokens:
        limitations.append("profile-cap-selected")

    return StrategySelectionDecision(
        version=STRATEGY_SELECTION_VERSION,
        status="pass" if ready else "fail",
        ready=ready,
        strategy=SELECTED_STRATEGY if ready else "disabled",
        profile=profile,
        rollout_percent=evidence.rollout_percent if ready else 0,
        effective_context_tokens=evidence.effective_context_tokens if ready else 0,
        blockers=tuple(blockers),
        limitations=tuple(limitations),
        metadata={
            "content_redacted": True,
            "deterministic": True,
            "default_strategy": "disabled",
            "automatic_runtime_activation": False,
            "explicit_opt_in_required": True,
            "kill_switch_supported": True,
            "quality_evidence_inherited_from_activation_policy": True,
            "profile_budget_required": True,
            "max_rollout_percent": 5,
            "runtime_auto_hook": False,
            "provider_policy_modified": False,
            "prompt_policy_modified": False,
            "quality_gate_modified": False,
            "translation_quality_improvement_claimed": False,
            "provider_latency_improvement_claimed": False,
        },
    )
