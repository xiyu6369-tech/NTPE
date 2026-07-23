from dataclasses import replace

import pytest

from core.controlled_runtime_atomic_authorization_consumption import AtomicAuthorizationConsumer
from . import build_context


def test_authentic_preparation_is_durably_consumed_not_executed(tmp_path):
    context = build_context(tmp_path)
    result = AtomicAuthorizationConsumer().consume(**context)
    assert result.status == "durably_consumed_not_executed"
    assert result.atomic_claim_committed is True
    assert result.claim.authorization_consumed is True
    assert result.claim.execution_started is False
    assert context["registry"].count_claims() == 1


def test_duplicate_is_deterministic_and_does_not_overwrite(tmp_path):
    context = build_context(tmp_path)
    consumer = AtomicAuthorizationConsumer()
    first = consumer.consume(**context)
    second = consumer.consume(**context)
    assert first.atomic_claim_committed is True
    assert second.status == "already_consumed"
    assert second.duplicate_claim_detected is True
    assert context["registry"].count_claims() == 1


def test_tampered_request_fails_before_registry_write(tmp_path):
    context = build_context(tmp_path)
    object.__setattr__(context["request"], "request_fingerprint", "0" * 64)
    result = AtomicAuthorizationConsumer().consume(**context)
    assert result.status == "invalid_request"
    assert not context["registry"].path.exists()


def test_broadened_scope_is_rejected(tmp_path):
    context = build_context(tmp_path)
    context["request"] = replace(context["request"], registry_scope="registry:other.sqlite3")
    result = AtomicAuthorizationConsumer().consume(**context)
    assert result.status == "invalid_request"


@pytest.mark.parametrize("field,value", (
    ("caller_confirmation", False),
    ("claim_for_single_execution", False),
    ("requested_unit_count", 0), ("requested_unit_count", 2),
    ("authorization_id", "different-authorization"),
    ("authorization_request_fingerprint", "0" * 64),
    ("authorization_decision_fingerprint", "1" * 64),
    ("execution_plan_fingerprint", "2" * 64),
    ("stage62_request_fingerprint", "3" * 64),
    ("stage62_record_fingerprint", "4" * 64),
    ("selected_adapter_index", 9),
))
def test_policy_relevant_request_changes_fail_before_write(tmp_path, field, value):
    context = build_context(tmp_path)
    context["request"] = replace(context["request"], **{field: value})
    result = AtomicAuthorizationConsumer().consume(**context)
    assert result.status != "durably_consumed_not_executed"
    assert result.atomic_claim_committed is False


@pytest.mark.parametrize("field,value", (
    ("authorization_consumption_prepared", False),
    ("authorization_consumed", True),
    ("authorization_reusable", True),
    ("durable_reuse_prevention_established", True),
    ("persistent_registry_written", True),
    ("execution_started", True),
    ("execution_completed", True),
))
def test_ineligible_stage62_states_fail_closed(tmp_path, field, value):
    context = build_context(tmp_path)
    context["stage62_record"] = replace(context["stage62_record"], **{field: value})
    result = AtomicAuthorizationConsumer().consume(**context)
    assert result.status == "upstream_contract_mismatch"
    assert not context["registry"].path.exists()


@pytest.mark.parametrize("field,value", (
    ("authorized", False), ("status", "rejected"),
    ("authorization_consumed", True), ("authorization_reusable", True),
))
def test_ineligible_stage61_states_fail_closed(tmp_path, field, value):
    context = build_context(tmp_path)
    context["authorization_decision"] = replace(context["authorization_decision"], **{field: value})
    assert AtomicAuthorizationConsumer().consume(**context).atomic_claim_committed is False
