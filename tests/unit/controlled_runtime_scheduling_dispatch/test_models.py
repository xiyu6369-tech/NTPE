from dataclasses import FrozenInstanceError, fields

import pytest

from core.controlled_runtime_scheduling_dispatch import (
    ControlledRuntimeDispatchPackage,
    ControlledRuntimeExecutionSchedule,
    ControlledRuntimeScheduler,
    ControlledRuntimeSchedulingDispatchVerificationResult,
    ControlledRuntimeSchedulingRequest,
    ControlledRuntimeSchedulingResult,
)
from core.controlled_runtime_scheduling_dispatch.policy import (
    DISPATCH_SCHEMA_NAME,
    REQUEST_SCHEMA_NAME,
    RESULT_SCHEMA_NAME,
    SCHEDULE_SCHEMA_NAME,
    VERIFICATION_SCHEMA_NAME,
)
from tests.unit.controlled_runtime_scheduling_dispatch import build_context


def test_request_is_immutable_deterministic_and_exact(tmp_path):
    first = build_context(tmp_path)
    request = first["request"]
    second = ControlledRuntimeSchedulingRequest(
        **{field.name: getattr(request, field.name) for field in fields(request) if field.init}
    )
    assert request == second
    assert request.schema_name == REQUEST_SCHEMA_NAME
    assert len(request.upstream_chain) == 35
    with pytest.raises(FrozenInstanceError):
        request.unit_scope = 2


@pytest.mark.parametrize("scope,error", [(True, TypeError), (1.0, TypeError), ("1", TypeError), (0, ValueError), (-1, ValueError), (2, ValueError)])
def test_unit_scope_is_strict(tmp_path, scope, error):
    context = build_context(tmp_path)
    request = context["request"]
    values = {field.name: getattr(request, field.name) for field in fields(request) if field.init}
    values["unit_scope"] = scope
    with pytest.raises(error):
        ControlledRuntimeSchedulingRequest(**values)


def test_success_models_are_immutable_and_versioned(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeScheduler().schedule(**context)
    assert isinstance(result, ControlledRuntimeSchedulingResult)
    assert isinstance(result.schedule, ControlledRuntimeExecutionSchedule)
    assert isinstance(result.dispatch_package, ControlledRuntimeDispatchPackage)
    assert result.schema_name == RESULT_SCHEMA_NAME
    assert result.schedule.schema_name == SCHEDULE_SCHEMA_NAME
    assert result.dispatch_package.schema_name == DISPATCH_SCHEMA_NAME
    assert len(result.dispatch_package.canonical_chain) == 38
    assert result.schedule.queue_record_consumed
    assert result.schedule.runtime_execution_scheduled
    assert result.dispatch_package.dispatch_package_created
    assert not result.schedule.execution_started
    with pytest.raises(FrozenInstanceError):
        result.schedule.execution_started = True


def test_verification_result_is_immutable_and_versioned():
    result = ControlledRuntimeSchedulingDispatchVerificationResult(
        valid=False,
        schema_verified=False,
        identity_verified=False,
        fingerprint_verified=False,
        upstream_verified=False,
        binding_verified=False,
        intent_verified=False,
        chain_verified=False,
        state_verified=False,
        persistence_verified=False,
        schedule_readback_verified=False,
        dispatch_readback_verified=False,
        canonical_payload_verified=False,
        zero_side_effects_verified=False,
        reason_codes=("INVALID_SCHEMA",),
    )
    assert result.schema_name == VERIFICATION_SCHEMA_NAME
    with pytest.raises(FrozenInstanceError):
        result.valid = True
