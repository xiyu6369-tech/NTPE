from dataclasses import FrozenInstanceError, replace

import pytest

from core.controlled_runtime_queue_admission_record_consumption import (
    ControlledRuntimeQueueAdmissionRecordConsumer,
    ControlledRuntimeQueueAdmissionRecordConsumptionPolicy,
)
from core.controlled_runtime_queue_admission_record_consumption.policy import (
    ADMISSION_CLASS,
    BOUNDARY_KIND,
    CLAIM_SCHEMA_NAME,
    CONSUMPTION_INTENT,
    PRIORITY_CLASS,
    REQUEST_SCHEMA_NAME,
    RESULT_SCHEMA_NAME,
    SUCCESS_STATUS,
    VERIFICATION_SCHEMA_NAME,
)
from core.controlled_runtime_queue_admission_record_consumption.serialization import (
    canonical_json,
)
from tests.unit.controlled_runtime_queue_admission_record_consumption import (
    build_context,
)


def test_models_are_frozen_and_schemas_are_exact(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmissionRecordConsumer().consume(**context)
    claim = result.claim

    assert claim is not None
    assert context["request"].schema_name == REQUEST_SCHEMA_NAME
    assert claim.schema_name == CLAIM_SCHEMA_NAME
    assert result.schema_name == RESULT_SCHEMA_NAME
    assert result.status == SUCCESS_STATUS
    for model in (context["request"], claim, result):
        with pytest.raises(FrozenInstanceError):
            model.schema_name = "changed"


def test_deterministic_request_and_claim_identities(tmp_path):
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    left_root.mkdir()
    right_root.mkdir()
    left_context = build_context(left_root)
    right_context = build_context(right_root)

    assert left_context["request"] == right_context["request"]
    assert left_context["request"].consumption_request_id.startswith(
        "stage613-record-consumption-request-"
    )
    assert len(left_context["request"].request_fingerprint) == 64

    left = ControlledRuntimeQueueAdmissionRecordConsumer().consume(**left_context)
    right = ControlledRuntimeQueueAdmissionRecordConsumer().consume(**right_context)
    assert left.claim == right.claim
    assert left.claim is not None
    assert left.claim.consumption_claim_id.startswith(
        "stage613-record-consumption-claim-"
    )
    assert len(left.claim.claim_fingerprint) == 64


def test_exact_policy_and_canonical_newlines(tmp_path):
    policy = ControlledRuntimeQueueAdmissionRecordConsumptionPolicy()
    request = build_context(tmp_path)["request"]

    assert policy.upstream_chain_layers == 31
    assert policy.complete_chain_layers == 33
    assert request.consumption_intent == CONSUMPTION_INTENT
    assert request.runtime_boundary_kind == BOUNDARY_KIND
    assert request.admission_class == ADMISSION_CLASS
    assert request.priority_class == PRIORITY_CLASS
    assert canonical_json({"文字": "甲\r\n乙\r丙"}) == canonical_json(
        {"文字": "甲\n乙\n丙"}
    )


@pytest.mark.parametrize("scope", [True, False, 0, -1, 2, 1.0, "1"])
def test_unit_scope_is_strict_integer_one(tmp_path, scope):
    with pytest.raises((TypeError, ValueError)):
        build_context(tmp_path, unit_scope=scope)


@pytest.mark.parametrize(
    "field,value",
    [
        ("consumption_intent", "wrong"),
        ("runtime_boundary_kind", "wrong"),
        ("admission_class", "wrong"),
        ("priority_class", "wrong"),
        ("ordering_key", ""),
    ],
)
def test_exact_request_constants_are_enforced(tmp_path, field, value):
    with pytest.raises(ValueError):
        build_context(tmp_path, **{field: value})


@pytest.mark.parametrize("kind", ["missing", "extra", "duplicate", "reordered"])
def test_request_chain_shape_and_content_tamper(tmp_path, kind):
    context = build_context(tmp_path)
    chain = list(context["request"].upstream_chain)
    if kind == "missing":
        chain.pop()
    elif kind == "extra":
        chain.append(chain[-1])
    elif kind == "duplicate":
        chain[1] = chain[0]
    else:
        chain[0], chain[1] = chain[1], chain[0]

    if len(chain) != 31:
        with pytest.raises(ValueError):
            replace(context["request"], upstream_chain=tuple(chain))
    else:
        tampered = replace(context["request"], upstream_chain=tuple(chain))
        context["request"] = tampered
        result = ControlledRuntimeQueueAdmissionRecordConsumer().consume(**context)
        assert not result.verification_succeeded
        assert result.claim is None


def test_verification_schema_constant_is_exact():
    assert VERIFICATION_SCHEMA_NAME == (
        "ntpe.controlled_runtime_queue_admission_record_consumption_verification_result"
    )
