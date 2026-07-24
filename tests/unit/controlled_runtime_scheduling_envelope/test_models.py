from dataclasses import FrozenInstanceError, replace

import pytest

import core.controlled_runtime_scheduling_envelope as package
from core.controlled_runtime_scheduling_envelope import (
    ControlledRuntimeSchedulingEnvelopeBuilder,
)
from core.controlled_runtime_scheduling_envelope.models import (
    ENVELOPE_SCHEMA_NAME,
    ENVELOPE_SCHEMA_VERSION,
    REQUEST_SCHEMA_NAME,
    REQUEST_SCHEMA_VERSION,
    ControlledRuntimeSchedulingEnvelopeFinding,
)
from . import build_context


def test_exact_public_api():
    assert package.__all__ == [
        "ControlledRuntimeSchedulingEnvelopeRequest",
        "ControlledRuntimeSchedulingEnvelope",
        "ControlledRuntimeSchedulingEnvelopeResult",
        "ControlledRuntimeSchedulingEnvelopePolicy",
        "ControlledRuntimeSchedulingEnvelopeBuilder",
        "verify_controlled_runtime_scheduling_envelope",
    ]
    assert not hasattr(package, "canonical_json")
    assert not hasattr(package, "ControlledRuntimeSchedulingEnvelopeFinding")


def test_models_findings_and_chain_are_immutable(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeSchedulingEnvelopeBuilder().build(**context)
    envelope = result.scheduling_envelope
    assert envelope is not None
    finding = ControlledRuntimeSchedulingEnvelopeFinding("x", "x", "x")
    for value, field in (
        (context["request"], "schema_name"),
        (envelope, "schema_name"),
        (result, "status"),
        (finding, "code"),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(value, field, "changed")
    with pytest.raises(TypeError):
        envelope.upstream_fingerprint_chain[0] = "0" * 64


def test_exact_request_and_envelope_schema(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeSchedulingEnvelopeBuilder().build(**context)
    assert context["request"].schema_name == REQUEST_SCHEMA_NAME
    assert context["request"].schema_version == REQUEST_SCHEMA_VERSION == "1.0"
    assert result.scheduling_envelope.schema_name == ENVELOPE_SCHEMA_NAME
    assert (
        result.scheduling_envelope.schema_version
        == ENVELOPE_SCHEMA_VERSION
        == "1.0"
    )


@pytest.mark.parametrize(
    "field,value,error",
    (
        ("scheduling_envelope_id", "", ValueError),
        ("scheduling_envelope_id", "not valid", ValueError),
        (
            "scheduling_envelope_id",
            "123e4567-e89b-12d3-a456-426614174000",
            ValueError,
        ),
        ("requested_schedule_unit_count", 0, ValueError),
        ("requested_schedule_unit_count", 2, ValueError),
        ("requested_schedule_unit_count", True, TypeError),
        ("caller_confirmation", False, ValueError),
        ("caller_confirmation", 1, TypeError),
        ("prepare_scheduling_envelope", False, ValueError),
        ("prepare_scheduling_envelope", 1, TypeError),
        ("queue_admission_requested", True, ValueError),
        ("queue_write_requested", True, ValueError),
        ("job_creation_requested", True, ValueError),
        ("worker_start_requested", True, ValueError),
        ("runtime_execution_requested", True, ValueError),
        ("provider_execution_requested", True, ValueError),
        ("translation_execution_requested", True, ValueError),
        ("runtime_boundary_kind", "wrong", ValueError),
        ("schema_name", "wrong", ValueError),
        ("schema_version", "2.0", ValueError),
    ),
)
def test_invalid_request_values_are_rejected(
    tmp_path,
    field,
    value,
    error,
):
    request = build_context(tmp_path)["request"]
    with pytest.raises(error):
        replace(request, **{field: value})


def test_unicode_crlf_and_canonical_serialization_are_deterministic(tmp_path):
    request = build_context(tmp_path)["request"]
    same = replace(request, purpose="Stage 6.8 測試\r\nmetadata")
    assert request == same
    assert request.to_json() == same.to_json()
    assert request.request_fingerprint == same.request_fingerprint
