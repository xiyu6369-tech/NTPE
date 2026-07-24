from dataclasses import FrozenInstanceError, fields

import pytest

from core.controlled_runtime_queue_admission_authorization import *
from core.controlled_runtime_queue_admission_authorization.policy import *
from core.controlled_runtime_queue_admission_authorization.serialization import canonical_json
from tests.unit.controlled_runtime_queue_admission_authorization import build_context


def test_models_are_frozen_and_schemas_exact(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmissionAuthorizer().authorize(**context)
    verification = verify_controlled_runtime_queue_admission_authorization(
        result.decision, request=context["request"],
        stage69_claim=context["stage69_claim"], stage69_request=context["stage69_request"],
        stage69_result=context["stage69_result"],
        stage69_verification_context=context["stage69_verification_context"],
    )
    assert (context["request"].schema_name, context["request"].schema_version) == (REQUEST_SCHEMA_NAME, "1.0")
    assert (result.decision.schema_name, result.decision.schema_version) == (DECISION_SCHEMA_NAME, "1.0")
    assert (result.schema_name, result.schema_version) == (RESULT_SCHEMA_NAME, "1.0")
    assert verification.schema_name == VERIFICATION_SCHEMA_NAME and verification.valid
    for model in (context["request"], result.decision, result, verification):
        with pytest.raises(FrozenInstanceError):
            model.schema_name = "changed"


def test_unicode_and_newlines_are_canonical():
    assert canonical_json({"文字": "甲\r\n乙\r丙"}) == canonical_json({"文字": "甲\n乙\n丙"})


def test_nested_public_structures_are_tuples(tmp_path):
    result = ControlledRuntimeQueueAdmissionAuthorizer().authorize(**build_context(tmp_path))
    assert isinstance(result.request.upstream_chain, tuple)
    assert isinstance(result.decision.canonical_chain, tuple)
    assert isinstance(result.decision.reason_codes, tuple)
    assert isinstance(result.reason_codes, tuple)
