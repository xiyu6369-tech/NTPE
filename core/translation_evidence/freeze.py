from __future__ import annotations

from dataclasses import dataclass
from typing import Final

EVIDENCE_FREEZE_VERSION: Final[str] = "6.0.0-stage11.6"
EVIDENCE_RELEASE_LINE: Final[str] = "TE-v6.0"
EVIDENCE_FROZEN_STAGES: Final[tuple[str, ...]] = (
    "stage11.1-translation-evidence-foundation",
    "stage11.2-source-translation-semantic-alignment",
    "stage11.3-evidence-to-retry-integration",
    "stage11.4-safe-targeted-merge-validation",
    "stage11.5-evidence-runtime-integration-audit",
)


@dataclass(frozen=True)
class TranslationEvidenceFreeze:
    version: str = EVIDENCE_FREEZE_VERSION
    release_line: str = EVIDENCE_RELEASE_LINE
    frozen: bool = True
    stages: tuple[str, ...] = EVIDENCE_FROZEN_STAGES
    provider_calls_added: int = 0
    prompt_text_changed: bool = False
    prompt_token_profile_changed: bool = False
    quality_score_changed: bool = False
    quality_decision_changed: bool = False
    retry_tier_changed: bool = False
    provider_budget_changed: bool = False
    timeout_changed: bool = False
    resume_changed: bool = False
    fail_closed: bool = True

    def to_metadata(self) -> dict[str, object]:
        return {
            "version": self.version,
            "release_line": self.release_line,
            "frozen": self.frozen,
            "stages": list(self.stages),
            "compatibility": {
                "provider_calls_added": self.provider_calls_added,
                "prompt_text_changed": self.prompt_text_changed,
                "prompt_token_profile_changed": self.prompt_token_profile_changed,
                "quality_score_changed": self.quality_score_changed,
                "quality_decision_changed": self.quality_decision_changed,
                "retry_tier_changed": self.retry_tier_changed,
                "provider_budget_changed": self.provider_budget_changed,
                "timeout_changed": self.timeout_changed,
                "resume_changed": self.resume_changed,
                "fail_closed": self.fail_closed,
            },
        }


def build_translation_evidence_freeze() -> TranslationEvidenceFreeze:
    return TranslationEvidenceFreeze()
