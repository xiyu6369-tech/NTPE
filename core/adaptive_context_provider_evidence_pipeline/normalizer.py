from __future__ import annotations

from core.adaptive_context_provider_evidence import ProviderTimingEvidence

from .model import ProviderEvidenceAttempt

_SUCCESS = {"success", "accepted"}


def normalize_attempt(record: ProviderTimingEvidence) -> ProviderEvidenceAttempt:
    usage = record.token_usage
    return ProviderEvidenceAttempt(
        attempt_number=record.attempt,
        attempt_status=record.status if record.status in _SUCCESS else "failed",
        elapsed_milliseconds=record.elapsed_ms,
        retry_count=max(0, record.attempt - 1),
        fallback_used=record.fallback_used,
        timeout=record.error_category == "timeout",
        http_503=record.http_status == 503,
        external_condition_failure=record.external_provider_condition,
        estimated_input_tokens=usage.estimated_input_tokens,
        estimated_output_tokens=usage.estimated_output_tokens,
        suspicious_short_output=record.suspicious_short_output,
        timing_complete=record.timing_complete,
    )
