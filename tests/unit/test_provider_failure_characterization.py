from dataclasses import FrozenInstanceError

import pytest

from core.provider_failure_characterization import (
    FAILURE_TYPES,
    DecisionInput,
    FailureType,
    classify_failure,
    execution_decision,
    execution_policy,
)


EXPECTED_TYPES = (
    "timeout", "connection_error", "dns_failure", "tls_failure",
    "authentication_failure", "authorization_failure", "quota_exceeded",
    "rate_limited", "provider_503", "provider_5xx", "provider_4xx",
    "invalid_request", "invalid_response", "truncated_response",
    "policy_refusal", "semantic_failure", "manual_block", "internal_error", "unknown",
)


def test_failure_taxonomy_v1_is_complete_fixed_and_ordered():
    assert FAILURE_TYPES == EXPECTED_TYPES
    assert tuple(item.value for item in FailureType) == EXPECTED_TYPES


@pytest.mark.parametrize(("evidence", "expected"), [
    ({"response_status_classification": "timeout"}, FailureType.TIMEOUT),
    ({"http_status": 503}, FailureType.PROVIDER_503),
    ({"http_status": 429}, FailureType.RATE_LIMITED),
    ({"http_status": 401}, FailureType.AUTHENTICATION_FAILURE),
    ({"http_status": 403}, FailureType.AUTHORIZATION_FAILURE),
    ({"error": "provider policy refusal"}, FailureType.POLICY_REFUSAL),
    ({"semantic_verification_outcome": "semantic_failed"}, FailureType.SEMANTIC_FAILURE),
    ({"reason_codes": ["RuntimeError"]}, FailureType.INTERNAL_ERROR),
    ({"message": "unrecognized condition"}, FailureType.UNKNOWN),
    ({"error": "DNS name resolution failed"}, FailureType.DNS_FAILURE),
    ({"error": "TLS certificate validation failed"}, FailureType.TLS_FAILURE),
    ({"http_status": 502}, FailureType.PROVIDER_5XX),
    ({"http_status": 404}, FailureType.PROVIDER_4XX),
    ({"http_status": 400}, FailureType.INVALID_REQUEST),
])
def test_classifier_rules_are_deterministic(evidence, expected):
    first = classify_failure(evidence)
    second = classify_failure(dict(reversed(tuple(evidence.items()))))
    assert first == second
    assert first.failure_type is expected
    assert first.classification == expected.value and first.deterministic


def test_explicit_failure_type_has_priority_over_text_or_http_status():
    result = classify_failure({"failure_type": "manual_block", "http_status": 503, "error": "timeout"})
    assert result.failure_type is FailureType.MANUAL_BLOCK


def test_all_execution_policies_are_immutable_fail_closed_and_evidence_only():
    for failure_type in FailureType:
        policy = execution_policy(failure_type)
        assert policy.retry_allowed is False
        assert policy.fallback_allowed is False
        assert policy.manual_review_required is True
        assert policy.evidence_only is True
        assert policy.execution_consumed is True
        assert policy.production_safe is True
    with pytest.raises(FrozenInstanceError):
        execution_policy(FailureType.TIMEOUT).retry_allowed = True


@pytest.mark.parametrize("failure_type", [FailureType.TIMEOUT, FailureType.RATE_LIMITED, FailureType.PROVIDER_503])
def test_timeout_429_and_503_policy_forbid_retry_and_fallback(failure_type):
    policy = execution_policy(failure_type)
    assert not policy.retry_allowed and not policy.fallback_allowed
    assert policy.manual_review_required and policy.execution_consumed


def test_decision_engine_consumes_claim_and_requires_manual_provider_investigation():
    decision = execution_decision(DecisionInput(
        failure_type=FailureType.TIMEOUT,
        authorization_consumed=True,
        execution_claim_consumed=True,
        provider_request_count=1,
    ))
    assert decision.status == "manual_review_required"
    assert decision.execution_consumed and decision.authorization_consumed
    assert not decision.retry_allowed and not decision.fallback_allowed
    assert decision.manual_review_required and decision.provider_investigation_required
    assert decision.production_safe
    assert decision.actions == (
        "execution_complete", "manual_review_required", "execution_consumed",
        "retry_forbidden", "fallback_forbidden", "provider_investigation_required",
    )


def test_semantic_candidate_requires_rollback_but_never_automatic_execution():
    decision = execution_decision(DecisionInput(
        failure_type=FailureType.SEMANTIC_FAILURE,
        authorization_consumed=True,
        execution_claim_consumed=True,
        provider_request_count=2,
        candidate_available=True,
        semantic_verification_run=True,
    ))
    assert decision.rollback_required and "rollback_required" in decision.actions
    assert not decision.retry_allowed and not decision.fallback_allowed


def test_production_modification_fails_production_safe_without_mutating_anything():
    decision = execution_decision(DecisionInput(
        failure_type=FailureType.INTERNAL_ERROR,
        authorization_consumed=False,
        execution_claim_consumed=False,
        provider_request_count=0,
        production_modified=True,
    ))
    assert decision.production_safe is False


@pytest.mark.parametrize("count", [-1, 1.5, "1"])
def test_invalid_provider_request_count_fails_closed(count):
    with pytest.raises(ValueError):
        execution_decision(DecisionInput(
            failure_type=FailureType.UNKNOWN,
            authorization_consumed=False,
            execution_claim_consumed=False,
            provider_request_count=count,
        ))

