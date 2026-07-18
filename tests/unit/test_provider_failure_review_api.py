from dataclasses import FrozenInstanceError

import pytest

from core.provider_failure_characterization import FailureType, summarize_execution


def record(**changes):
    value = {
        "execution_id": "exec-1",
        "provider": "nvidia",
        "model": "model-1",
        "response_status_classification": "timeout",
        "provider_requests": 1,
        "network_requests": 1,
        "authorization_consumed": True,
        "execution_claim_path": "isolated/claim.json",
        "review_artifact_path": None,
        "semantic_verification_outcome": "not_run_provider_failed",
        "formal_output_changed": False,
        "resume_changed": False,
        "cache_changed": False,
        "character_store_changed": False,
        "context_store_changed": False,
    }
    value.update(changes)
    return value


def test_execution_summary_is_immutable_complete_and_read_only():
    source = record()
    before = dict(source)
    summary = summarize_execution(source)
    assert source == before
    assert summary.failure_type is FailureType.TIMEOUT
    assert summary.classification == "timeout"
    assert summary.authorization_consumed and summary.execution_consumed
    assert not summary.candidate_available and not summary.semantic_verification_run
    assert not summary.rollback_required and summary.manual_review_required
    assert summary.production_safe and not summary.retry_allowed and not summary.fallback_allowed
    assert summary.batch108_provider_requests_added == summary.batch108_network_requests_added == 0
    with pytest.raises(FrozenInstanceError):
        summary.production_safe = False


def test_candidate_and_semantic_state_are_derived_without_writes():
    summary = summarize_execution(record(
        response_status_classification="semantic_failure",
        review_artifact_path="isolated/review.json",
        semantic_verification_outcome="semantic_failed",
        provider_requests=2,
        network_requests=2,
    ))
    assert summary.candidate_available and summary.semantic_verification_run
    assert summary.rollback_required


@pytest.mark.parametrize(("field", "value"), [
    ("provider_requests", -1), ("provider_requests", "1"),
    ("network_requests", -1), ("network_requests", 1.5),
])
def test_summary_rejects_invalid_request_evidence(field, value):
    with pytest.raises(ValueError):
        summarize_execution(record(**{field: value}))


def test_summary_fingerprint_is_order_independent():
    item = record()
    reversed_item = dict(reversed(tuple(item.items())))
    assert summarize_execution(item).evidence_fingerprint == summarize_execution(reversed_item).evidence_fingerprint

