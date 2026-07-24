from dataclasses import FrozenInstanceError, fields

import pytest

import core.controlled_runtime_handoff_boundary as public
from core.controlled_runtime_handoff_boundary.models import (
    ControlledRuntimeHandoffFinding,
)
from tests.unit.controlled_runtime_handoff_boundary.test_boundary import (
    accept,
    build_inputs,
)


def test_exact_public_api():
    assert public.__all__ == (
        "ControlledRuntimeHandoffRequest",
        "ControlledRuntimeHandoffReceipt",
        "ControlledRuntimeHandoffResult",
        "ControlledRuntimeHandoffPolicy",
        "ControlledRuntimeHandoffBoundary",
        "verify_runtime_handoff_receipt",
    )
    assert "ControlledRuntimeHandoffFinding" not in public.__all__


def test_models_findings_and_tuple_fields_are_immutable():
    result = accept()
    objects = (
        result.request, result.receipt, result,
        ControlledRuntimeHandoffFinding("X", "blocking", "x"),
    )
    for obj in objects:
        with pytest.raises(FrozenInstanceError):
            obj.schema_version = "2.0"
    with pytest.raises(TypeError):
        result.receipt.upstream_fingerprint_chain[0] = "x"


def test_exact_schemas_and_no_sensitive_payload_fields():
    result = accept()
    assert result.request.schema_name == "ntpe.controlled_runtime_handoff_request"
    assert result.receipt.schema_name == "ntpe.controlled_runtime_handoff_receipt"
    names = {
        field.name for model in (result.request, result.receipt)
        for field in fields(model)
    }
    assert names.isdisjoint({
        "source_text", "prompt_text", "provider_payload", "credentials",
        "translated_output", "timestamp", "hostname", "username", "process_id",
    })


@pytest.mark.parametrize("name,value,error", (
    ("handoff_id", "", ValueError),
    ("handoff_id", "bad id", ValueError),
    ("runtime_boundary_id", "", ValueError),
    ("runtime_boundary_id", "bad id", ValueError),
    ("runtime_boundary_kind", "scheduler", ValueError),
    ("caller_confirmation", False, ValueError),
    ("caller_confirmation", 1, TypeError),
    ("handoff_requested", False, ValueError),
    ("handoff_requested", 1, TypeError),
    ("scheduling_requested", True, ValueError),
    ("execution_requested", True, ValueError),
    ("provider_requested", True, ValueError),
    ("translation_requested", True, ValueError),
    ("requested_unit_count", 0, ValueError),
    ("requested_unit_count", 2, ValueError),
    ("requested_unit_count", True, TypeError),
    ("schema_name", "wrong", ValueError),
    ("schema_version", "2.0", ValueError),
))
def test_invalid_request_model_rejected(name, value, error):
    inputs = build_inputs()
    payload = inputs["request"]._fingerprint_payload()
    payload[name] = value
    with pytest.raises(error):
        type(inputs["request"])(**payload)


def test_unicode_crlf_and_mapping_order_are_deterministic():
    left = build_inputs()["request"]
    right = build_inputs()["request"]
    assert left.request_fingerprint == right.request_fingerprint
    assert left.to_json() == right.to_json()
