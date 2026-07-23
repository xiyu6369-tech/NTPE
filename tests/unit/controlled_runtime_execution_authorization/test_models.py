from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass

import pytest

import core.controlled_runtime_execution_authorization as public_api
from core.controlled_runtime_execution_authorization import (
    ControlledRuntimeExecutionAuthorizationDecision,
    ControlledRuntimeExecutionAuthorizationRequest,
    ControlledRuntimeExecutionAuthorizationResult,
    ControlledRuntimeExecutionAuthorizationPolicy,
)
from core.controlled_runtime_execution_authorization.models import (
    ControlledRuntimeExecutionAuthorizationFinding,
)
from core.controlled_runtime_execution_authorization.policy import (
    DECISION_SCHEMA_NAME,
    DECISION_SCHEMA_VERSION,
    REQUEST_SCHEMA_NAME,
    REQUEST_SCHEMA_VERSION,
)
from tests.unit.controlled_runtime_execution_authorization import (
    build_plan,
    build_request,
)


def test_public_models_are_frozen_dataclasses() -> None:
    for model in (
        ControlledRuntimeExecutionAuthorizationRequest,
        ControlledRuntimeExecutionAuthorizationDecision,
        ControlledRuntimeExecutionAuthorizationResult,
        ControlledRuntimeExecutionAuthorizationFinding,
        ControlledRuntimeExecutionAuthorizationPolicy,
    ):
        assert is_dataclass(model)
        assert model.__dataclass_params__.frozen


def test_request_is_immutable_canonical_and_schema_exact(tmp_path) -> None:
    request = build_request(build_plan(tmp_path))
    with pytest.raises(FrozenInstanceError):
        request.purpose = "changed"  # type: ignore[misc]
    assert request.schema_name == REQUEST_SCHEMA_NAME
    assert request.schema_version == REQUEST_SCHEMA_VERSION
    assert request.to_json() == request.to_json()
    assert "\r" not in request.to_json()


def test_collection_inputs_and_outputs_are_immutable(tmp_path) -> None:
    plan = build_plan(tmp_path)
    with pytest.raises(TypeError):
        build_request(plan, requested_adapter_indices=[0])
    request = build_request(
        plan,
        requested_adapter_indices=(0,),
        requested_plan_step_fingerprints=(
            plan.steps[0].execution_step_fingerprint,
        ),
    )
    assert isinstance(request.requested_adapter_indices, tuple)
    assert isinstance(request.requested_plan_step_fingerprints, tuple)


def test_decision_schema_constants_are_exact() -> None:
    assert (
        DECISION_SCHEMA_NAME
        == "ntpe.controlled_runtime_execution_authorization_decision"
    )
    assert DECISION_SCHEMA_VERSION == "1.0"


def test_only_required_symbols_are_exported() -> None:
    assert public_api.__all__ == [
        "ControlledRuntimeExecutionAuthorizationRequest",
        "ControlledRuntimeExecutionAuthorizationDecision",
        "ControlledRuntimeExecutionAuthorizationResult",
        "ControlledRuntimeExecutionAuthorizer",
        "ControlledRuntimeExecutionAuthorizationPolicy",
    ]
    assert all(not name.startswith("_") for name in public_api.__all__)
    assert "ControlledRuntimeExecutionAuthorizationFinding" not in public_api.__all__


def test_required_request_fields_are_present() -> None:
    names = {field.name for field in fields(ControlledRuntimeExecutionAuthorizationRequest)}
    assert {
        "authorization_id",
        "execution_plan_fingerprint",
        "selected_adapter_index",
        "requested_provider_request_limit",
        "requested_translation_request_limit",
        "retry_requested",
        "fallback_requested",
        "output_replacement_requested",
        "runtime_execution_requested",
        "provider_execution_requested",
        "network_execution_requested",
        "translation_execution_requested",
        "caller_confirmation",
        "authorization_scope",
        "purpose",
        "schema_name",
        "schema_version",
        "request_fingerprint",
    } <= names

