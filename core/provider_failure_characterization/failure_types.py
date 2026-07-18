from __future__ import annotations

from enum import Enum


class FailureType(str, Enum):
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    DNS_FAILURE = "dns_failure"
    TLS_FAILURE = "tls_failure"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_FAILURE = "authorization_failure"
    QUOTA_EXCEEDED = "quota_exceeded"
    RATE_LIMITED = "rate_limited"
    PROVIDER_503 = "provider_503"
    PROVIDER_5XX = "provider_5xx"
    PROVIDER_4XX = "provider_4xx"
    INVALID_REQUEST = "invalid_request"
    INVALID_RESPONSE = "invalid_response"
    TRUNCATED_RESPONSE = "truncated_response"
    POLICY_REFUSAL = "policy_refusal"
    SEMANTIC_FAILURE = "semantic_failure"
    MANUAL_BLOCK = "manual_block"
    INTERNAL_ERROR = "internal_error"
    UNKNOWN = "unknown"


FAILURE_TYPES = tuple(item.value for item in FailureType)

