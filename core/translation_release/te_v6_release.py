from __future__ import annotations

from typing import Final

from .release_contract import TEV6ReleaseContract

TE_V6_STABLE_VERSION: Final[str] = "6.0.0"
TE_V6_RELEASE_CHANNEL: Final[str] = "stable"
TE_V6_FROZEN: Final[bool] = True

TE_V6_FROZEN_STAGES: Final[tuple[str, ...]] = (
    "01", "02", "03", "04", "05", "06", "07", "08", "08.1", "09",
    "10", "10.1", "10.1.1", "10.2", "10.3", "11.1", "11.2", "11.3",
    "11.4", "11.5", "11.6", "12.1", "12.2", "12.3", "12.4", "12.4.1", "12.5",
)

PROVIDER_INVARIANTS: Final[tuple[str, ...]] = (
    "nvidia-provider", "meta/llama-3.3-70b-instruct", "40-rpm-ceiling",
    "timeout-propagation", "provider-attempts", "retry-wait", "503-backpressure",
    "provider-budget", "provider-request-accounting",
)
PROMPT_INVARIANTS: Final[tuple[str, ...]] = (
    "prompt-compiler", "prompt-discipline", "translation-discipline-policy",
    "naturalness-policy", "single-injection-source", "prompt-token-observability",
    "NTPE_PROMPT_DISCIPLINE", "NTPE_ADAPTIVE_PROMPT_FEEDBACK",
    "NTPE_NATURALNESS_POLICY", "rollback",
)
QUALITY_INVARIANTS: Final[tuple[str, ...]] = (
    "quality-v5", "legacy-qa-adapter", "unified-quality-gate", "score-decision-schema",
    "smart-local-repair", "adaptive-local-repair", "blocking-warning-boundary",
    "best-attempt-selection", "provider-retry-fallback", "semantic-repetition-guard",
    "completeness-guard", "unsupported-detail-guard",
)
RETRY_INVARIANTS: Final[tuple[str, ...]] = (
    "local_repair", "targeted_retry", "full_retry", "reject", "provider-budget",
    "targeted-retry-evidence-required", "fail-closed-merge", "best-attempt-fallback",
    "legacy-segment-recovery", "resume",
)
EVIDENCE_INVARIANTS: Final[tuple[str, ...]] = (
    "evidence-model", "alignment-offsets", "monotonic-mapping", "reliability-confidence",
    "evidence-to-retry", "safe-targeted-merge", "evidence-audit",
    "unreliable-evidence-cannot-authorize-targeted-retry",
)
NATURALNESS_INVARIANTS: Final[tuple[str, ...]] = (
    "period-appropriate-fluent-traditional-chinese", "no-forced-taiwan-localization",
    "faithfulness-before-naturalness", "safe-canonicalization", "hallucination-guard",
    "literary-collocation-guard", "voice-register-guard", "no-subjective-rewriting",
)


def build_te_v6_release_contract(*, production_validated: bool = True) -> TEV6ReleaseContract:
    return TEV6ReleaseContract(
        version=TE_V6_STABLE_VERSION, channel=TE_V6_RELEASE_CHANNEL, frozen=TE_V6_FROZEN,
        discipline_frozen=True, evidence_frozen=True, naturalness_frozen=True,
        provider_contract_frozen=True, prompt_contract_frozen=True, quality_contract_frozen=True,
        retry_contract_frozen=True, resume_contract_frozen=True, backward_compatible=True,
        production_validated=production_validated,
        metadata={
            "frozen_stages": TE_V6_FROZEN_STAGES,
            "provider_calls_added": 0, "provider_client_created": False,
            "http_requests_added": 0, "nvidia_api_called": False,
            "active_generation_rule_count": 8, "voice_register_feedback_only": True,
            "quality_score_changed": False, "unified_decision_changed": False,
        },
    )
