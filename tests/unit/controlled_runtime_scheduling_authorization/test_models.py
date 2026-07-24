from dataclasses import FrozenInstanceError, fields

import pytest

import core.controlled_runtime_scheduling_authorization as public
from core.controlled_runtime_scheduling_authorization.models import (
    ControlledRuntimeSchedulingAuthorizationFinding,
)
from tests.unit.controlled_runtime_scheduling_authorization.test_authorizer import (
    authorize,
    build_inputs,
)


def test_exact_public_api_and_internal_helpers_hidden():
    assert public.__all__ == (
        "ControlledRuntimeSchedulingAuthorizationRequest",
        "ControlledRuntimeSchedulingAuthorizationDecision",
        "ControlledRuntimeSchedulingAuthorizationResult",
        "ControlledRuntimeSchedulingAuthorizationPolicy",
        "ControlledRuntimeSchedulingAuthorizer",
        "verify_scheduling_authorization_decision",
    )
    assert "ControlledRuntimeSchedulingAuthorizationFinding" not in public.__all__
    assert "canonical_json" not in public.__all__


def test_models_findings_and_tuple_chain_are_immutable():
    result = authorize()
    objects = (
        result.request, result.decision, result,
        ControlledRuntimeSchedulingAuthorizationFinding("X", "blocking", "x"),
    )
    for obj in objects:
        with pytest.raises(FrozenInstanceError):
            obj.schema_version = "2.0"
    with pytest.raises(TypeError):
        result.decision.upstream_fingerprint_chain[0] = "x"


def test_exact_schemas_and_no_sensitive_fields():
    result = authorize()
    assert (
        result.request.schema_name
        == "ntpe.controlled_runtime_scheduling_authorization_request"
    )
    assert (
        result.decision.schema_name
        == "ntpe.controlled_runtime_scheduling_authorization_decision"
    )
    names = {
        item.name for model in (result.request, result.decision)
        for item in fields(model)
    }
    assert names.isdisjoint({
        "source_text", "prompt_text", "provider_payload", "credentials",
        "translated_output", "timestamp", "hostname", "username",
        "process_id", "memory_address",
    })


@pytest.mark.parametrize("name,value,error", (
    ("scheduling_authorization_id", "", ValueError),
    ("scheduling_authorization_id", "bad id", ValueError),
    ("scheduling_authorization_id",
     "123e4567-e89b-12d3-a456-426614174000", ValueError),
    ("caller_confirmation", False, ValueError),
    ("caller_confirmation", 1, TypeError),
    ("scheduling_authorization_requested", False, ValueError),
    ("scheduling_authorization_requested", 1, TypeError),
    ("schedule_once", False, ValueError),
    ("schedule_once", 1, TypeError),
    ("queue_creation_requested", True, ValueError),
    ("job_creation_requested", True, ValueError),
    ("worker_start_requested", True, ValueError),
    ("runtime_execution_requested", True, ValueError),
    ("provider_execution_requested", True, ValueError),
    ("translation_execution_requested", True, ValueError),
    ("requested_schedule_unit_count", 0, ValueError),
    ("requested_schedule_unit_count", 2, ValueError),
    ("requested_schedule_unit_count", True, TypeError),
    ("runtime_boundary_kind", "scheduler", ValueError),
    ("schema_name", "wrong", ValueError),
    ("schema_version", "2.0", ValueError),
))
def test_invalid_request_model_rejected(name, value, error):
    payload = build_inputs()["request"]._fingerprint_payload()
    payload[name] = value
    with pytest.raises(error):
        type(build_inputs()["request"])(**payload)


def test_serialization_unicode_crlf_and_mapping_order_are_deterministic():
    left = build_inputs()["request"]
    right = build_inputs()["request"]
    assert left.request_fingerprint == right.request_fingerprint
    assert left.to_json() == right.to_json()
    assert "測試" in left.to_json()
    assert "\\r\\n" in left.to_json()
