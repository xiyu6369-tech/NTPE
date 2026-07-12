from __future__ import annotations

from .model import ActivationEvidence, ActivationPolicyDecision, ActivationPolicyRequest

POLICY_VERSION = "7.0.0-stage08.1"
ALLOWED_PROFILES = ("literary", "novel")
MAX_STAGE081_ROLLOUT_PERCENT = 5


def evaluate_activation_policy(
    evidence: ActivationEvidence,
    request: ActivationPolicyRequest,
) -> ActivationPolicyDecision:
    blockers: list[str] = []
    limitations: list[str] = []
    profile = str(request.profile or "").strip().lower()
    rollout = max(0, min(100, int(request.rollout_percent)))

    if request.kill_switch:
        blockers.append("kill-switch-enabled")
    if not request.explicitly_enabled:
        blockers.append("explicit-enable-required")
    if profile not in ALLOWED_PROFILES:
        blockers.append("profile-not-allowed")
    if rollout <= 0:
        blockers.append("rollout-percent-required")
    if rollout > MAX_STAGE081_ROLLOUT_PERCENT:
        blockers.append("rollout-percent-exceeds-stage-limit")
    if not evidence.ab_ready or evidence.ab_status != "pass":
        blockers.append("ab-quality-gate-not-ready")
    if evidence.canary_activated_records != 1:
        blockers.append("single-canary-activation-required")
    if evidence.estimated_tokens_saved <= 0:
        blockers.append("positive-token-saving-required")
    if evidence.provider_calls_added != 0:
        blockers.append("provider-call-increase-detected")
    if not evidence.target_chunk_completed:
        blockers.append("target-chunk-not-complete")
    if evidence.fallback_reasons:
        blockers.append("canary-fallback-present")
    if evidence.canary_status not in {"pass", "pass_with_external_provider_limitation"}:
        blockers.append("canary-status-not-eligible")
    if evidence.canary_status == "pass_with_external_provider_limitation":
        limitations.append("external-provider-limitation-observed")

    blockers = list(dict.fromkeys(blockers))
    ready = not blockers
    return ActivationPolicyDecision(
        version=POLICY_VERSION,
        status="pass" if ready else "fail",
        ready=ready,
        mode="production_canary" if ready else "disabled",
        profile=profile,
        rollout_percent=rollout if ready else 0,
        blockers=tuple(blockers),
        limitations=tuple(limitations),
        metadata={
            "content_redacted": True,
            "default_mode": "disabled",
            "automatic_activation": False,
            "explicit_opt_in_required": True,
            "kill_switch_supported": True,
            "max_stage081_rollout_percent": MAX_STAGE081_ROLLOUT_PERCENT,
            "provider_policy_modified": False,
            "prompt_policy_modified": False,
            "runtime_auto_hook": False,
            "translation_quality_improvement_claimed": False,
            "provider_latency_improvement_claimed": False,
        },
    )
