from __future__ import annotations

from .config import BUDGET_VERSION, POLICY_VERSION, SELECTED_STRATEGY, STRATEGY_VERSION
from .model import ProductionEvidence, RolloutConfig
from .sampling import MAX_ROLLOUT_PERCENT

ALLOWED_PROFILES = ("literary", "novel")


def production_blockers(config: RolloutConfig, evidence: ProductionEvidence, *, kill_switch: bool = False) -> tuple[str, ...]:
    blockers = list(evidence.blockers)
    profile = str(config.profile).strip().lower()
    if not config.enabled:
        blockers.append("production-opt-in-required")
    if config.kill_switch or kill_switch:
        blockers.append("kill-switch-enabled")
    if profile not in ALLOWED_PROFILES:
        blockers.append("profile-not-allowed")
    if config.rollout_percent <= 0:
        blockers.append("rollout-percent-required")
    if config.rollout_percent > MAX_ROLLOUT_PERCENT:
        blockers.append("rollout-percent-exceeds-stage-limit")
    if evidence.policy_version != POLICY_VERSION or not evidence.policy_ready or evidence.policy_status != "pass":
        blockers.append("activation-policy-not-ready")
    if evidence.policy_mode != "production_canary":
        blockers.append("activation-policy-mode-not-eligible")
    if evidence.budget_version != BUDGET_VERSION or not evidence.budget_ready or evidence.budget_status != "pass":
        blockers.append("profile-budget-not-ready")
    if evidence.strategy_version != STRATEGY_VERSION or not evidence.strategy_ready or evidence.strategy_status != "pass":
        blockers.append("strategy-not-ready")
    if evidence.strategy != SELECTED_STRATEGY:
        blockers.append("strategy-not-eligible")
    profiles = {profile, evidence.policy_profile, evidence.budget_profile, evidence.strategy_profile}
    if len(profiles) != 1:
        blockers.append("profile-evidence-mismatch")
    percents = {config.rollout_percent, evidence.policy_rollout_percent, evidence.strategy_rollout_percent}
    if len(percents) != 1:
        blockers.append("rollout-evidence-mismatch")
    if evidence.effective_context_tokens <= 0 or evidence.strategy_context_tokens != evidence.effective_context_tokens:
        blockers.append("budget-evidence-mismatch")
    if not evidence.evidence_fresh:
        blockers.append("stale-evidence")
    if not evidence.evidence_integrity:
        blockers.append("production-artifact-integrity-failure")
    return tuple(dict.fromkeys(blockers))
