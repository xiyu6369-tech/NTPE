from __future__ import annotations

from collections.abc import Mapping

from .failure_types import FailureType
from .schema import FailureClassification


_ALIASES = {
    "timeout": FailureType.TIMEOUT,
    "connect_timeout": FailureType.TIMEOUT,
    "read_timeout": FailureType.TIMEOUT,
    "provider_timeout": FailureType.TIMEOUT,
    "connection_error": FailureType.CONNECTION_ERROR,
    "connection_failed": FailureType.CONNECTION_ERROR,
    "dns_failure": FailureType.DNS_FAILURE,
    "dns_error": FailureType.DNS_FAILURE,
    "tls_failure": FailureType.TLS_FAILURE,
    "ssl_error": FailureType.TLS_FAILURE,
    "authentication_failure": FailureType.AUTHENTICATION_FAILURE,
    "authentication_error": FailureType.AUTHENTICATION_FAILURE,
    "authorization_failure": FailureType.AUTHORIZATION_FAILURE,
    "permission_denied": FailureType.AUTHORIZATION_FAILURE,
    "quota_exceeded": FailureType.QUOTA_EXCEEDED,
    "resource_exhausted": FailureType.QUOTA_EXCEEDED,
    "rate_limited": FailureType.RATE_LIMITED,
    "rate_limit": FailureType.RATE_LIMITED,
    "provider_503": FailureType.PROVIDER_503,
    "provider_5xx": FailureType.PROVIDER_5XX,
    "provider_4xx": FailureType.PROVIDER_4XX,
    "invalid_request": FailureType.INVALID_REQUEST,
    "invalid_response": FailureType.INVALID_RESPONSE,
    "malformed_response": FailureType.INVALID_RESPONSE,
    "truncated_response": FailureType.TRUNCATED_RESPONSE,
    "policy_refusal": FailureType.POLICY_REFUSAL,
    "semantic_failure": FailureType.SEMANTIC_FAILURE,
    "semantic_failed": FailureType.SEMANTIC_FAILURE,
    "manual_block": FailureType.MANUAL_BLOCK,
    "blocked": FailureType.MANUAL_BLOCK,
    "internal_error": FailureType.INTERNAL_ERROR,
    "unknown": FailureType.UNKNOWN,
    "unknown_failure": FailureType.UNKNOWN,
}

_TEXT_RULES = (
    (("timeout", "timed out", "deadline exceeded"), FailureType.TIMEOUT),
    (("dns", "name resolution", "getaddrinfo"), FailureType.DNS_FAILURE),
    (("tls", "ssl", "certificate"), FailureType.TLS_FAILURE),
    (("authentication", "invalid api key", "unauthenticated"), FailureType.AUTHENTICATION_FAILURE),
    (("authorization", "permission denied", "forbidden"), FailureType.AUTHORIZATION_FAILURE),
    (("quota", "resource exhausted"), FailureType.QUOTA_EXCEEDED),
    (("rate limit", "too many requests"), FailureType.RATE_LIMITED),
    (("connection", "connection reset", "connection refused"), FailureType.CONNECTION_ERROR),
    (("truncated", "incomplete response"), FailureType.TRUNCATED_RESPONSE),
    (("refusal", "policy refusal", "cannot comply"), FailureType.POLICY_REFUSAL),
    (("semantic",), FailureType.SEMANTIC_FAILURE),
    (("invalid response", "malformed response", "response format"), FailureType.INVALID_RESPONSE),
    (("invalid request", "malformed request"), FailureType.INVALID_REQUEST),
    (("internal", "runtimeerror", "runtime error"), FailureType.INTERNAL_ERROR),
)


def _normalized(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _classification(failure_type: FailureType, reason: str, field: str) -> FailureClassification:
    return FailureClassification(failure_type, failure_type.value, reason, field)


def classify_failure(evidence: Mapping[str, object] | FailureType | str) -> FailureClassification:
    if isinstance(evidence, FailureType):
        return _classification(evidence, "explicit_failure_type", "failure_type")
    if isinstance(evidence, str):
        alias = _ALIASES.get(_normalized(evidence))
        return _classification(alias or FailureType.UNKNOWN, "explicit_string" if alias else "unrecognized_string", "input")
    if not isinstance(evidence, Mapping):
        return _classification(FailureType.UNKNOWN, "unsupported_evidence_type", "input")

    for field in ("failure_type", "response_status_classification", "classification", "outcome"):
        raw = _normalized(evidence.get(field))
        if raw in _ALIASES:
            return _classification(_ALIASES[raw], f"matched_{field}", field)

    status = evidence.get("http_status")
    if isinstance(status, int):
        if status == 401:
            return _classification(FailureType.AUTHENTICATION_FAILURE, "http_401", "http_status")
        if status == 403:
            return _classification(FailureType.AUTHORIZATION_FAILURE, "http_403", "http_status")
        if status == 429:
            return _classification(FailureType.RATE_LIMITED, "http_429", "http_status")
        if status == 503:
            return _classification(FailureType.PROVIDER_503, "http_503", "http_status")
        if 500 <= status <= 599:
            return _classification(FailureType.PROVIDER_5XX, "http_5xx", "http_status")
        if status == 400:
            return _classification(FailureType.INVALID_REQUEST, "http_400", "http_status")
        if 400 <= status <= 499:
            return _classification(FailureType.PROVIDER_4XX, "http_4xx", "http_status")

    text = " ".join(str(evidence.get(field) or "") for field in ("reason", "error", "message", "reason_codes")).lower()
    for markers, failure_type in _TEXT_RULES:
        if any(marker in text for marker in markers):
            return _classification(failure_type, "matched_text_rule", "reason_text")
    if evidence.get("semantic_verification_outcome") in {"semantic_failed", "failed"}:
        return _classification(FailureType.SEMANTIC_FAILURE, "semantic_outcome_failed", "semantic_verification_outcome")
    if evidence.get("manual_block") is True:
        return _classification(FailureType.MANUAL_BLOCK, "manual_block_true", "manual_block")
    return _classification(FailureType.UNKNOWN, "no_rule_matched", "none")

