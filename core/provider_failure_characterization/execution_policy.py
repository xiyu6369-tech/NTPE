from __future__ import annotations

from types import MappingProxyType

from .failure_types import FailureType
from .schema import FailureExecutionPolicy


_ROLLBACK_FAILURES = {
    FailureType.INVALID_RESPONSE,
    FailureType.TRUNCATED_RESPONSE,
    FailureType.SEMANTIC_FAILURE,
}
_PROVIDER_INVESTIGATION_FAILURES = {
    FailureType.TIMEOUT,
    FailureType.CONNECTION_ERROR,
    FailureType.DNS_FAILURE,
    FailureType.TLS_FAILURE,
    FailureType.QUOTA_EXCEEDED,
    FailureType.RATE_LIMITED,
    FailureType.PROVIDER_503,
    FailureType.PROVIDER_5XX,
    FailureType.INVALID_RESPONSE,
    FailureType.TRUNCATED_RESPONSE,
    FailureType.INTERNAL_ERROR,
    FailureType.UNKNOWN,
}


def _build_policy(failure_type: FailureType) -> FailureExecutionPolicy:
    return FailureExecutionPolicy(
        failure_type=failure_type,
        retry_allowed=False,
        fallback_allowed=False,
        manual_review_required=True,
        evidence_only=True,
        execution_consumed=True,
        rollback_required=failure_type in _ROLLBACK_FAILURES,
        production_safe=True,
        provider_investigation_required=failure_type in _PROVIDER_INVESTIGATION_FAILURES,
    )


EXECUTION_POLICIES = MappingProxyType({item: _build_policy(item) for item in FailureType})


def execution_policy(failure_type: FailureType | str) -> FailureExecutionPolicy:
    item = failure_type if isinstance(failure_type, FailureType) else FailureType(failure_type)
    return EXECUTION_POLICIES[item]

