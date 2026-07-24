from dataclasses import FrozenInstanceError, replace

import pytest

import core.controlled_runtime_atomic_scheduling_consumption as package
from core.controlled_runtime_atomic_scheduling_consumption import (
    AtomicSchedulingAuthorizationConsumer,
)
from core.controlled_runtime_atomic_scheduling_consumption.models import (
    CLAIM_SCHEMA_NAME,
    CLAIM_SCHEMA_VERSION,
    REQUEST_SCHEMA_NAME,
    REQUEST_SCHEMA_VERSION,
    AtomicSchedulingConsumptionFinding,
)
from . import build_context, build_request


def test_exact_public_api_and_private_rows_not_exported():
    assert package.__all__ == [
        "AtomicSchedulingAuthorizationConsumptionRequest",
        "AtomicSchedulingAuthorizationConsumptionClaim",
        "AtomicSchedulingAuthorizationConsumptionResult",
        "AtomicSchedulingAuthorizationConsumptionPolicy",
        "AtomicSchedulingAuthorizationConsumptionRegistry",
        "AtomicSchedulingAuthorizationConsumer",
        "verify_atomic_scheduling_consumption_claim",
    ]
    assert not hasattr(package, "_CLAIM_COLUMNS")
    assert not hasattr(package, "canonical_json")


def test_request_claim_result_findings_and_chain_are_immutable(tmp_path):
    context = build_context(tmp_path)
    request = context["request"]
    result = AtomicSchedulingAuthorizationConsumer().consume(**context)
    assert result.claim is not None
    for value in (request, result.claim, result, AtomicSchedulingConsumptionFinding("x", "x", "x")):
        with pytest.raises(FrozenInstanceError):
            value.schema_name = "changed"
    with pytest.raises(TypeError):
        result.claim.upstream_fingerprint_chain[0] = "0" * 64


def test_exact_request_and_claim_schema(tmp_path):
    context = build_context(tmp_path)
    result = AtomicSchedulingAuthorizationConsumer().consume(**context)
    assert context["request"].schema_name == REQUEST_SCHEMA_NAME
    assert context["request"].schema_version == REQUEST_SCHEMA_VERSION == "1.0"
    assert result.claim.schema_name == CLAIM_SCHEMA_NAME
    assert result.claim.schema_version == CLAIM_SCHEMA_VERSION == "1.0"


@pytest.mark.parametrize("field,value,error", (
    ("scheduling_consumption_id", "", ValueError),
    ("scheduling_consumption_id", "not valid", ValueError),
    ("scheduling_consumption_id", "123e4567-e89b-12d3-a456-426614174000", ValueError),
    ("requested_schedule_unit_count", 0, ValueError),
    ("requested_schedule_unit_count", 2, ValueError),
    ("requested_schedule_unit_count", True, TypeError),
    ("caller_confirmation", False, ValueError),
    ("caller_confirmation", 1, TypeError),
    ("consume_scheduling_authorization", False, ValueError),
    ("consume_scheduling_authorization", 1, TypeError),
    ("queue_creation_requested", True, ValueError),
    ("job_creation_requested", True, ValueError),
    ("worker_start_requested", True, ValueError),
    ("runtime_execution_requested", True, ValueError),
    ("provider_execution_requested", True, ValueError),
    ("translation_execution_requested", True, ValueError),
    ("registry_namespace", "wrong", ValueError),
    ("runtime_boundary_kind", "wrong", ValueError),
    ("schema_name", "wrong", ValueError),
    ("schema_version", "2.0", ValueError),
))
def test_invalid_request_values_are_rejected(tmp_path, field, value, error):
    context = build_context(tmp_path)
    request = context["request"]
    with pytest.raises(error):
        replace(request, **{field: value})


def test_canonical_serialization_is_deterministic_for_unicode_crlf_and_mapping_order(tmp_path):
    left = build_context(tmp_path)["request"]
    right = replace(left, purpose="Stage 6.7 測試\r\nmetadata")
    assert left == right
    assert left.to_json() == right.to_json()
    assert left.request_fingerprint == right.request_fingerprint