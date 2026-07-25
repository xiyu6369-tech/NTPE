from dataclasses import FrozenInstanceError, fields

import pytest

from core.controlled_runtime_queue_admission import (
    ControlledRuntimeQueueAdmitter,
    ControlledRuntimeQueueAdmissionPolicy,
)
from core.controlled_runtime_queue_admission.models import (
    ControlledRuntimeQueueAdmissionRequest,
    ControlledRuntimeQueueAdmissionResult,
    ControlledRuntimeQueueRecord,
    ControlledRuntimeQueueRecordVerificationResult,
)
from core.controlled_runtime_queue_admission.policy import (
    ADMISSION_INTENT,
    QUEUE_RECORD_SCHEMA_NAME,
    REQUEST_SCHEMA_NAME,
    RESULT_SCHEMA_NAME,
    VERIFICATION_SCHEMA_NAME,
)
from core.controlled_runtime_queue_admission.serialization import canonical_json
from tests.unit.controlled_runtime_queue_admission import build_context


def test_all_public_models_are_frozen_and_schemas_are_exact(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmitter().admit(**context)
    record = result.queue_record
    assert record is not None
    assert context["request"].schema_name == REQUEST_SCHEMA_NAME
    assert record.schema_name == QUEUE_RECORD_SCHEMA_NAME
    assert result.schema_name == RESULT_SCHEMA_NAME
    verification = ControlledRuntimeQueueRecordVerificationResult(
        valid=True,
        schema_verified=True,
        identity_verified=True,
        fingerprint_verified=True,
        upstream_verified=True,
        binding_verified=True,
        intent_verified=True,
        chain_verified=True,
        state_verified=True,
        persistence_verified=True,
        durable_readback_verified=True,
        canonical_payload_verified=True,
        reason_codes=(),
    )
    assert verification.schema_name == VERIFICATION_SCHEMA_NAME
    for model in (context["request"], record, result, verification):
        with pytest.raises(FrozenInstanceError):
            model.schema_name = "changed"


def test_request_and_record_are_deterministic_across_roots(tmp_path):
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    left_root.mkdir()
    right_root.mkdir()
    left = build_context(left_root)
    right = build_context(right_root)
    assert left["request"] == right["request"]
    left_result = ControlledRuntimeQueueAdmitter().admit(**left)
    right_result = ControlledRuntimeQueueAdmitter().admit(**right)
    assert left_result.queue_record == right_result.queue_record
    assert left["request"].admission_request_id.startswith(
        "stage71-queue-admission-request-"
    )
    assert left_result.queue_record is not None
    assert left_result.queue_record.queue_record_id.startswith(
        "stage71-runtime-queue-record-"
    )


@pytest.mark.parametrize("scope", [True, False, 0, -1, 2, 1.0, "1"])
def test_unit_scope_is_strict_integer_one(tmp_path, scope):
    with pytest.raises((TypeError, ValueError)):
        build_context(tmp_path, unit_scope=scope)


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("schema_name", "wrong"),
        ("schema_version", "2.0"),
        ("runtime_boundary_kind", "wrong"),
        ("admission_class", "wrong"),
        ("priority_class", "wrong"),
        ("ordering_key", ""),
        ("admission_intent", "wrong"),
    ],
)
def test_request_constants_and_schema_fail_closed(tmp_path, field_name, value):
    with pytest.raises(ValueError):
        build_context(tmp_path, **{field_name: value})


@pytest.mark.parametrize("kind", ["missing", "extra", "duplicate", "reordered"])
def test_request_chain_shape_fails_closed(tmp_path, kind):
    base = build_context(tmp_path)
    chain = list(base["request"].upstream_chain)
    if kind == "missing":
        chain.pop()
    elif kind == "extra":
        chain.append("0" * 64)
    elif kind == "duplicate":
        chain[1] = chain[0]
    else:
        chain[0], chain[1] = chain[1], chain[0]
    isolated = tmp_path / kind
    isolated.mkdir()
    if kind == "reordered":
        context = build_context(isolated, upstream_chain=tuple(chain))
        result = ControlledRuntimeQueueAdmitter().admit(**context)
        assert not result.verification_succeeded
        assert result.queue_record is None
    else:
        with pytest.raises(ValueError):
            build_context(isolated, upstream_chain=tuple(chain))


def test_exact_intent_policy_layers_and_canonical_newlines(tmp_path):
    context = build_context(tmp_path)
    policy = ControlledRuntimeQueueAdmissionPolicy()
    assert context["request"].admission_intent == ADMISSION_INTENT
    assert (
        policy.upstream_chain_layers,
        policy.request_chain_layers,
        policy.complete_chain_layers,
    ) == (33, 34, 35)
    assert canonical_json({"文字": "甲\r\n乙\r丙"}) == canonical_json(
        {"文字": "甲\n乙\n丙"}
    )


def test_exact_model_field_contracts():
    request_names = tuple(
        item.name for item in fields(ControlledRuntimeQueueAdmissionRequest)
    )
    record_names = tuple(item.name for item in fields(ControlledRuntimeQueueRecord))
    result_names = tuple(
        item.name for item in fields(ControlledRuntimeQueueAdmissionResult)
    )
    assert request_names[-4:] == (
        "schema_name",
        "schema_version",
        "admission_request_id",
        "request_fingerprint",
    )
    assert record_names[-4:] == (
        "schema_name",
        "schema_version",
        "queue_record_id",
        "queue_record_fingerprint",
    )
    assert result_names[:4] == (
        "request",
        "queue_record",
        "verification_succeeded",
        "upstream_verified",
    )
