from __future__ import annotations

from dataclasses import dataclass
from typing import Final

DISCIPLINE_FREEZE_VERSION: Final[str] = "6.0.0-stage08"
DISCIPLINE_RELEASE_LINE: Final[str] = "TE-v6.0"
DISCIPLINE_FROZEN_STAGES: Final[tuple[str, ...]] = (
    "stage01-discipline-architecture-foundation",
    "stage02-discipline-policy-activation",
    "stage03-discipline-quality-enforcement",
    "stage04-adaptive-local-repair-framework",
    "stage05-adaptive-retry-decision-engine",
    "stage06-discipline-runtime-orchestrator",
    "stage07-discipline-observability-audit-trail",
)


@dataclass(frozen=True)
class TranslationDisciplineFreeze:
    version: str = DISCIPLINE_FREEZE_VERSION
    release_line: str = DISCIPLINE_RELEASE_LINE
    frozen: bool = True
    stages: tuple[str, ...] = DISCIPLINE_FROZEN_STAGES
    provider_calls_added: int = 0
    prompt_text_changed: bool = False
    prompt_token_profile_changed: bool = False
    quality_score_changed: bool = False
    quality_decision_changed: bool = False
    timeout_changed: bool = False
    retry_policy_changed: bool = False
    resume_changed: bool = False

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
                "timeout_changed": self.timeout_changed,
                "retry_policy_changed": self.retry_policy_changed,
                "resume_changed": self.resume_changed,
            },
        }


def build_translation_discipline_freeze() -> TranslationDisciplineFreeze:
    return TranslationDisciplineFreeze()
