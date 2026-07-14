from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from core.adaptive_context_provider_evidence import ProviderTimingEvidence

from .config import FROZEN_OUTPUT_TOKEN_BUDGET


@dataclass(frozen=True)
class ControlledRetryTokenEvidence:
    estimated_input_tokens: int
    estimated_output_token_budget: int
    actual_input_tokens: int | None
    actual_output_tokens: int | None
    token_usage_source: str
    token_usage_complete: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def prepared_token_evidence() -> ControlledRetryTokenEvidence:
    return ControlledRetryTokenEvidence(
        estimated_input_tokens=0,
        estimated_output_token_budget=FROZEN_OUTPUT_TOKEN_BUDGET,
        actual_input_tokens=None,
        actual_output_tokens=None,
        token_usage_source="not_executed",
        token_usage_complete=False,
    )


def token_evidence_from_attempt(
    attempt: ProviderTimingEvidence | None,
) -> ControlledRetryTokenEvidence:
    if attempt is None:
        return prepared_token_evidence()
    usage = attempt.token_usage
    actual_input = usage.actual_input_tokens
    actual_output = usage.actual_output_tokens
    complete = actual_input is not None and actual_output is not None
    return ControlledRetryTokenEvidence(
        estimated_input_tokens=usage.estimated_input_tokens,
        estimated_output_token_budget=(
            usage.estimated_output_tokens or FROZEN_OUTPUT_TOKEN_BUDGET
        ),
        actual_input_tokens=actual_input,
        actual_output_tokens=actual_output,
        token_usage_source=usage.usage_source if complete else "estimate_only",
        token_usage_complete=complete,
    )
