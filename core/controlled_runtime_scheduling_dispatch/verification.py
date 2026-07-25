"""Official offline verification for Stage 7.2 schedule and dispatch."""

from __future__ import annotations

from .errors import ControlledRuntimeSchedulingDispatchVerificationError
from .models import (
    ControlledRuntimeDispatchPackage,
    ControlledRuntimeExecutionSchedule,
    ControlledRuntimeSchedulingDispatchVerificationResult,
    ControlledRuntimeSchedulingRequest,
    ControlledRuntimeSchedulingResult,
    _identity,
)
from .policy import (
    DISPATCH_SCHEMA_NAME,
    DISPATCH_SCHEMA_VERSION,
    REQUEST_SCHEMA_NAME,
    REQUEST_SCHEMA_VERSION,
    RESULT_SCHEMA_NAME,
    RESULT_SCHEMA_VERSION,
    SCHEDULE_SCHEMA_NAME,
    SCHEDULE_SCHEMA_VERSION,
    SCHEDULING_INTENT,
    ControlledRuntimeSchedulingPolicy,
)
from .serialization import canonical_sha256, values


def verify_controlled_runtime_scheduling_dispatch(
    schedule: ControlledRuntimeExecutionSchedule,
    dispatch_package: ControlledRuntimeDispatchPackage,
    *,
    request: ControlledRuntimeSchedulingRequest,
    result: ControlledRuntimeSchedulingResult,
    queue_record,
    stage71_request,
    stage71_result,
    stage613_claim,
    stage613_request,
    stage613_result,
    stage613_verification_context,
    persisted_schedule_payload_json: str | None = None,
    persisted_dispatch_payload_json: str | None = None,
    persistence_committed: bool = False,
    schedule_readback_verified: bool = False,
    dispatch_readback_verified: bool = False,
    raise_on_error: bool = False,
) -> ControlledRuntimeSchedulingDispatchVerificationResult:
    if not isinstance(request, ControlledRuntimeSchedulingRequest):
        raise TypeError("request must be a Stage 7.2 scheduling request")
    if not isinstance(schedule, ControlledRuntimeExecutionSchedule):
        raise TypeError("schedule must be a Stage 7.2 execution schedule")
    if not isinstance(dispatch_package, ControlledRuntimeDispatchPackage):
        raise TypeError("dispatch_package must be a Stage 7.2 dispatch package")
    if not isinstance(result, ControlledRuntimeSchedulingResult):
        raise TypeError("result must be a Stage 7.2 scheduling result")

    policy_denials = ControlledRuntimeSchedulingPolicy().evaluate(
        request,
        queue_record=queue_record,
        stage71_request=stage71_request,
        stage71_result=stage71_result,
        stage613_claim=stage613_claim,
        stage613_request=stage613_request,
        stage613_result=stage613_result,
        stage613_verification_context=stage613_verification_context,
    )
    schema_ok = all(
        (
            (request.schema_name, request.schema_version)
            == (REQUEST_SCHEMA_NAME, REQUEST_SCHEMA_VERSION),
            (schedule.schema_name, schedule.schema_version)
            == (SCHEDULE_SCHEMA_NAME, SCHEDULE_SCHEMA_VERSION),
            (dispatch_package.schema_name, dispatch_package.schema_version)
            == (DISPATCH_SCHEMA_NAME, DISPATCH_SCHEMA_VERSION),
            (result.schema_name, result.schema_version)
            == (RESULT_SCHEMA_NAME, RESULT_SCHEMA_VERSION),
        )
    )
    request_id = _identity(
        "stage72-scheduling-request",
        values(request, exclude=("scheduling_request_id", "request_fingerprint")),
    )
    request_fingerprint = canonical_sha256(
        values(request, exclude=("request_fingerprint",))
    )
    schedule_pre_chain = tuple(schedule.canonical_chain[:36])
    schedule_id = _identity(
        "stage72-runtime-execution-schedule",
        schedule._payload(schedule_pre_chain, schedule_id=""),
    )
    schedule_fingerprint = canonical_sha256(
        schedule._payload(schedule_pre_chain, schedule_id=schedule.schedule_id)
    )
    dispatch_pre_chain = tuple(dispatch_package.canonical_chain[:37])
    dispatch_id = _identity(
        "stage72-runtime-dispatch-package",
        dispatch_package._payload(
            dispatch_pre_chain, dispatch_package_id=""
        ),
    )
    dispatch_fingerprint = canonical_sha256(
        dispatch_package._payload(
            dispatch_pre_chain,
            dispatch_package_id=dispatch_package.dispatch_package_id,
        )
    )
    identity_ok = (
        request.scheduling_request_id == request_id
        and schedule.schedule_id == schedule_id
        and dispatch_package.dispatch_package_id == dispatch_id
    )
    fingerprint_ok = (
        request.request_fingerprint == request_fingerprint
        and schedule.schedule_fingerprint == schedule_fingerprint
        and dispatch_package.dispatch_fingerprint == dispatch_fingerprint
    )
    common = (
        "queue_record_id",
        "queue_record_fingerprint",
        "admission_request_id",
        "admission_request_fingerprint",
        "stage613_claim_id",
        "stage613_claim_fingerprint",
        "stage612_record_id",
        "stage612_record_fingerprint",
        "stage611_claim_id",
        "stage611_claim_fingerprint",
        "stage610_authorization_id",
        "stage610_decision_fingerprint",
        "stage69_consumption_claim_id",
        "stage69_claim_fingerprint",
        "stage68_scheduling_envelope_id",
        "stage68_envelope_fingerprint",
        "stage67_consumption_claim_id",
        "stage67_claim_fingerprint",
        "stage66_scheduling_authorization_id",
        "stage66_decision_fingerprint",
        "runtime_boundary_id",
        "runtime_boundary_kind",
        "selected_adapter_index",
        "capability_state_fingerprint",
        "admission_class",
        "priority_class",
        "ordering_key",
        "unit_scope",
        "execution_plan_reference_fingerprint",
        "work_package_reference_fingerprint",
    )
    binding_ok = all(
        getattr(request, name) == getattr(schedule, name)
        == getattr(dispatch_package, name)
        for name in common
    ) and all(
        (
            schedule.scheduling_request_id == request.scheduling_request_id,
            schedule.scheduling_request_fingerprint
            == request.request_fingerprint,
            dispatch_package.scheduling_request_id
            == request.scheduling_request_id,
            dispatch_package.scheduling_request_fingerprint
            == request.request_fingerprint,
            dispatch_package.schedule_id == schedule.schedule_id,
            dispatch_package.schedule_fingerprint
            == schedule.schedule_fingerprint,
            dispatch_package.dispatch_key == schedule.dispatch_key,
            result.request == request,
            result.schedule == schedule,
            result.dispatch_package == dispatch_package,
        )
    )
    expected_dispatch_key = canonical_sha256(
        {
            "queue_record_id": request.queue_record_id,
            "queue_record_fingerprint": request.queue_record_fingerprint,
            "ordering_key": request.ordering_key,
            "unit_scope": request.unit_scope,
        }
    )
    dispatch_key_ok = (
        schedule.dispatch_key == expected_dispatch_key
        and dispatch_package.dispatch_key == expected_dispatch_key
    )
    chain_ok = all(
        (
            len(request.upstream_chain) == 35,
            tuple(request.upstream_chain) == tuple(queue_record.canonical_chain),
            len(schedule.canonical_chain) == 37,
            tuple(schedule.canonical_chain[:35]) == tuple(request.upstream_chain),
            schedule.canonical_chain[35] == request.request_fingerprint,
            schedule.canonical_chain[36] == schedule.schedule_fingerprint,
            len(dispatch_package.canonical_chain) == 38,
            tuple(dispatch_package.canonical_chain[:37])
            == tuple(schedule.canonical_chain),
            dispatch_package.canonical_chain[37]
            == dispatch_package.dispatch_fingerprint,
            len(set(dispatch_package.canonical_chain)) == 38,
        )
    )
    state_ok = all(
        (
            schedule.queue_record_created is True,
            schedule.queue_record_consumed is True,
            schedule.queue_record_reusable is False,
            schedule.runtime_execution_scheduled is True,
            schedule.dispatch_package_created is True,
            dispatch_package.dispatch_package_created is True,
            result.queue_record_consumed is True,
            result.runtime_execution_scheduled is True,
            result.dispatch_package_created is True,
            all(
                getattr(item, name) is False
                for item in (schedule, dispatch_package)
                for name in (
                    "execution_started",
                    "runtime_executor_invoked",
                    "worker_started",
                    "provider_execution_started",
                    "translation_execution_started",
                    "output_written",
                )
            ),
        )
    )
    intent_ok = request.scheduling_intent == SCHEDULING_INTENT
    persistence_ok = type(persistence_committed) is bool and persistence_committed
    schedule_readback_ok = (
        type(schedule_readback_verified) is bool and schedule_readback_verified
    )
    dispatch_readback_ok = (
        type(dispatch_readback_verified) is bool and dispatch_readback_verified
    )
    payload_ok = (
        persisted_schedule_payload_json == schedule.to_json()
        and persisted_dispatch_payload_json == dispatch_package.to_json()
    )
    zero_names = (
        "runtime_execution_count",
        "worker_started_count",
        "provider_execution_count",
        "network_execution_count",
        "translation_execution_count",
        "output_write_count",
        "resume_write_count",
        "cache_write_count",
    )
    zero_ok = all(
        type(getattr(result, name)) is int and getattr(result, name) == 0
        for name in zero_names
    )
    checks = (
        ("INVALID_SCHEMA", schema_ok),
        ("INVALID_IDENTITY", identity_ok),
        ("FINGERPRINT_MISMATCH", fingerprint_ok),
        ("UPSTREAM_VERIFICATION_FAILED", not policy_denials),
        ("BINDING_MISMATCH", binding_ok),
        ("INVALID_DISPATCH_KEY", dispatch_key_ok),
        ("INVALID_INTENT", intent_ok),
        ("CHAIN_MISMATCH", chain_ok),
        ("INVARIANT_VIOLATION", state_ok and zero_ok),
        ("PERSISTENCE_NOT_PROVEN", persistence_ok),
        ("SCHEDULE_READBACK_NOT_PROVEN", schedule_readback_ok),
        ("DISPATCH_READBACK_NOT_PROVEN", dispatch_readback_ok),
        ("CANONICAL_PAYLOAD_MISMATCH", payload_ok),
    )
    reasons = tuple(
        dict.fromkeys(
            tuple(policy_denials)
            + tuple(code for code, valid in checks if not valid)
        )
    )
    verification = ControlledRuntimeSchedulingDispatchVerificationResult(
        valid=not reasons,
        schema_verified=schema_ok,
        identity_verified=identity_ok,
        fingerprint_verified=fingerprint_ok,
        upstream_verified=not policy_denials,
        binding_verified=binding_ok,
        intent_verified=intent_ok,
        chain_verified=chain_ok,
        state_verified=state_ok,
        persistence_verified=persistence_ok,
        schedule_readback_verified=schedule_readback_ok,
        dispatch_readback_verified=dispatch_readback_ok,
        canonical_payload_verified=payload_ok,
        zero_side_effects_verified=zero_ok,
        reason_codes=reasons,
    )
    if raise_on_error and verification.valid is not True:
        raise ControlledRuntimeSchedulingDispatchVerificationError(
            ",".join(verification.reason_codes)
        )
    return verification
