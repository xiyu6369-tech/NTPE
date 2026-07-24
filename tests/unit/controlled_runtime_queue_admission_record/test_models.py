from dataclasses import FrozenInstanceError, fields

import pytest

from core.controlled_runtime_queue_admission_record import *
from core.controlled_runtime_queue_admission_record.policy import *
from core.controlled_runtime_queue_admission_record.serialization import canonical_json
from tests.unit.controlled_runtime_queue_admission_record import build_context


def test_models_are_frozen_and_schemas_exact(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmissionRecordBuilder().prepare(**context)
    verification = verify_controlled_runtime_queue_admission_record(
        result.record, request=context["request"],
        stage611_claim=context["stage611_claim"],
        stage611_request=context["stage611_request"],
        stage611_result=context["stage611_result"],
        stage611_verification_context=context["stage611_verification_context"],
    )
    assert (context["request"].schema_name, context["request"].schema_version) == (
        REQUEST_SCHEMA_NAME, "1.0"
    )
    assert (result.record.schema_name, result.record.schema_version) == (
        RECORD_SCHEMA_NAME, "1.0"
    )
    assert (result.schema_name, result.schema_version) == (RESULT_SCHEMA_NAME, "1.0")
    assert verification.schema_name == VERIFICATION_SCHEMA_NAME and verification.valid
    for model in (context["request"], result.record, result, verification):
        with pytest.raises(FrozenInstanceError):
            model.schema_name = "changed"


def test_unicode_and_newlines_are_canonical():
    assert canonical_json({"文字": "甲\r\n乙\r丙"}) == canonical_json({"文字": "甲\n乙\n丙"})


def test_nested_public_structures_are_tuples(tmp_path):
    result = ControlledRuntimeQueueAdmissionRecordBuilder().prepare(**build_context(tmp_path))
    assert isinstance(result.request.upstream_chain, tuple)
    assert isinstance(result.record.canonical_chain, tuple)
    assert isinstance(result.record.admission_class, str)
    assert isinstance(result.record.priority_class, str)
    assert isinstance(result.reason_codes, tuple)


def test_deterministic_ids_and_fingerprints(tmp_path):
    a_dir = tmp_path / "a"
    a_dir.mkdir()
    b_dir = tmp_path / "b"
    b_dir.mkdir()
    a = build_context(a_dir)
    b = build_context(b_dir)
    assert a["request"].record_request_id.startswith("stage612-record-request-")
    assert len(a["request"].record_request_id) > len("stage612-record-request-")
    assert len(a["request"].request_fingerprint) == 64
    ra = ControlledRuntimeQueueAdmissionRecordBuilder().prepare(**a)
    rb = ControlledRuntimeQueueAdmissionRecordBuilder().prepare(**b)
    assert ra == rb
    assert ra.record.queue_admission_record_id.startswith("stage612-record-")
    assert len(ra.record.record_fingerprint) == 64
    assert len(ra.record.queue_admission_record_id) > len("stage612-record-")


@pytest.mark.parametrize("scope", [True, False, 0, -1, 2, 1.0, "1"])
def test_unit_scope_is_strict_one(tmp_path, scope):
    with pytest.raises((TypeError, ValueError)):
        build_context(tmp_path, unit_scope=scope)


def test_exact_intent_and_class_constants(tmp_path):
    context = build_context(tmp_path)
    assert context["request"].preparation_intent == PREPARATION_INTENT
    assert context["request"].admission_class == ADMISSION_CLASS
    assert context["request"].priority_class == PRIORITY_CLASS
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(ValueError):
        build_context(other, preparation_intent="wrong")
    other2 = tmp_path / "other2"
    other2.mkdir()
    with pytest.raises(ValueError):
        build_context(other2, admission_class="wrong")
    other3 = tmp_path / "other3"
    other3.mkdir()
    with pytest.raises(ValueError):
        build_context(other3, priority_class="wrong")
