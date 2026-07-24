from dataclasses import FrozenInstanceError, fields, replace

import pytest

from core.controlled_runtime_scheduling_envelope_consumption import (
    ControlledRuntimeSchedulingEnvelopeConsumptionClaim,
    ControlledRuntimeSchedulingEnvelopeConsumptionResult,
)
from core.controlled_runtime_scheduling_envelope_consumption.consumer import (
    ControlledRuntimeSchedulingEnvelopeConsumer,
)
from core.controlled_runtime_scheduling_envelope_consumption.policy import (
    CLAIM_SCHEMA_NAME,
    CLAIM_SCHEMA_VERSION,
    REQUEST_SCHEMA_NAME,
    REQUEST_SCHEMA_VERSION,
    RESULT_SCHEMA_NAME,
    RESULT_SCHEMA_VERSION,
)
from core.controlled_runtime_scheduling_envelope_consumption.serialization import (
    canonical_json,
)
from tests.unit.controlled_runtime_scheduling_envelope_consumption import (
    build_context,
)


def test_request_is_immutable_deterministic_and_exact_schema(tmp_path):
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    left_root.mkdir()
    right_root.mkdir()
    left = build_context(left_root)["request"]
    right = build_context(right_root)["request"]
    assert left == right
    assert (left.schema_name, left.schema_version) == (
        REQUEST_SCHEMA_NAME,
        REQUEST_SCHEMA_VERSION,
    )
    with pytest.raises(FrozenInstanceError):
        left.unit_scope = 2
    with pytest.raises(TypeError):
        left.upstream_fingerprint_chain[0] = "x"


@pytest.mark.parametrize("unit_scope", [True, False, 0, -1, 2, 1.0, "1"])
def test_unit_scope_is_strict_integer_one(tmp_path, unit_scope):
    with pytest.raises((TypeError, ValueError)):
        build_context(tmp_path, unit_scope=unit_scope)


def test_canonical_unicode_and_newline_normalization():
    left = canonical_json({"文字": "甲\r\n乙\r丙"})
    right = canonical_json({"文字": "甲\n乙\n丙"})
    assert left == right == '{"文字":"甲\\n乙\\n丙"}'


def test_success_models_are_frozen_and_have_exact_schemas(tmp_path):
    result = ControlledRuntimeSchedulingEnvelopeConsumer().consume(
        **build_context(tmp_path)
    )
    claim = result.claim
    assert claim is not None
    assert len(claim.canonical_chain) == 25
    assert claim.canonical_chain[-1] == claim.claim_fingerprint
    assert (claim.schema_name, claim.schema_version) == (
        CLAIM_SCHEMA_NAME,
        CLAIM_SCHEMA_VERSION,
    )
    assert (result.schema_name, result.schema_version) == (
        RESULT_SCHEMA_NAME,
        RESULT_SCHEMA_VERSION,
    )
    with pytest.raises(FrozenInstanceError):
        claim.unit_scope = 2
    with pytest.raises(FrozenInstanceError):
        result.status = "changed"


def test_claim_and_result_fields_are_explicit():
    claim_names = {item.name for item in fields(
        ControlledRuntimeSchedulingEnvelopeConsumptionClaim
    )}
    result_names = {item.name for item in fields(
        ControlledRuntimeSchedulingEnvelopeConsumptionResult
    )}
    assert {
        "consumption_claim_id",
        "claim_fingerprint",
        "canonical_chain",
        "scheduling_envelope_consumed",
        "queue_admission_authorized",
        "runtime_execution_scheduled",
    } <= claim_names
    assert {
        "verification_succeeded",
        "durable_claim_created",
        "replay_detected",
        "persistence_committed",
    } <= result_names


@pytest.mark.parametrize(
    "field,value",
    [
        ("scheduling_authorization_consumed", False),
        ("scheduling_envelope_prepared", False),
        ("scheduling_envelope_consumed", False),
        ("scheduling_envelope_reusable", True),
        ("queue_admission_authorized", True),
        ("runtime_execution_scheduled", True),
        ("queue_record_created", True),
        ("execution_started", True),
    ],
)
def test_claim_state_invariants_fail_closed(tmp_path, field, value):
    result = ControlledRuntimeSchedulingEnvelopeConsumer().consume(
        **build_context(tmp_path)
    )
    assert result.claim is not None
    with pytest.raises(ValueError):
        replace(result.claim, **{field: value})


