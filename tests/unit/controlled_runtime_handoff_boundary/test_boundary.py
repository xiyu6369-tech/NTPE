from dataclasses import replace

from core.controlled_runtime_execution_envelope import (
    ControlledRuntimeExecutionEnvelopeBuilder,
)
from core.controlled_runtime_execution_plan import (
    ControlledRuntimePreparationFreezeValidationResult,
)
from core.controlled_runtime_handoff_boundary import (
    ControlledRuntimeHandoffBoundary,
    ControlledRuntimeHandoffRequest,
)
from core.controlled_runtime_handoff_boundary.policy import exact_handoff_scope
from tests.integration import controlled_runtime_execution_envelope_contract_test as s64


def build_inputs(**request_overrides):
    plan = s64.make_plan()
    auth_request = s64.make_auth_request()
    auth_decision = s64._make_real_auth_decision()
    auth_result = s64.make_auth_result()
    stage62_request = s64.make_stage62_request()
    stage62_record = s64.make_stage62_record()
    stage62_chain = (
        plan.source.execution_package_fingerprint,
        auth_decision.upstream_authorization_decision_fingerprint,
        plan.source.approval_record_fingerprint,
        plan.source.runtime_submission_package_fingerprint,
        plan.source.runtime_adapter_request_fingerprint,
        plan.source.runtime_adapter_preparation_fingerprint,
        plan.execution_plan_fingerprint,
        auth_request.request_fingerprint,
        auth_decision.decision_fingerprint,
        stage62_request.request_fingerprint,
        "",
    )
    stage62_record = replace(
        stage62_record, consumed_unit_count=1,
        upstream_fingerprint_chain=stage62_chain,
        consumption_request_fingerprint=stage62_request.request_fingerprint,
    )
    stage62_record = replace(
        stage62_record,
        upstream_fingerprint_chain=stage62_chain[:-1]
        + (stage62_record.record_fingerprint,),
    )
    stage62_result = replace(
        s64.make_stage62_result(), request=stage62_request, record=stage62_record,
    )
    stage63_claim_request = s64.make_stage63_claim_request(
        stage62_request_fingerprint=stage62_request.request_fingerprint,
        stage62_record_fingerprint=stage62_record.record_fingerprint,
    )
    stage63_claim = s64.make_stage63_claim(
        stage62_request_fingerprint=stage62_request.request_fingerprint,
        stage62_record_fingerprint=stage62_record.record_fingerprint,
        upstream_fingerprint_chain=stage62_record.upstream_fingerprint_chain
        + (stage63_claim_request.request_fingerprint,),
        claim_request_fingerprint=stage63_claim_request.request_fingerprint,
    )
    stage63_result = s64._make_real_stage63_result(
        stage63_claim, stage63_claim_request
    )
    stage64_request = s64.make_request_from_claim(
        stage63_claim, stage63_claim_request,
        auth_request=auth_request, auth_decision=auth_decision,
    )
    stage64_request = replace(
        stage64_request,
        stage62_request_fingerprint=stage62_request.request_fingerprint,
        stage62_record_fingerprint=stage62_record.record_fingerprint,
    )
    stage64_result = ControlledRuntimeExecutionEnvelopeBuilder().build(
        request=stage64_request, plan=plan,
        activation_gate=s64._FREEZE_ACTIVATION_GATE,
        freeze_component=s64._FREEZE_COMPONENT,
        freeze_version=s64._FREEZE_VERSION,
        auth_request=auth_request, auth_decision=auth_decision,
        auth_result=auth_result, stage62_request=stage62_request,
        stage62_record=stage62_record, stage62_result=stage62_result,
        stage63_claim_request=stage63_claim_request,
        stage63_claim=stage63_claim, stage63_result=stage63_result,
    )
    envelope = stage64_result.envelope
    assert envelope is not None, [(f.code, f.field, f.observed) for f in stage64_result.policy_findings]
    boundary_id = "offline-runtime-boundary-001"
    kwargs = dict(
        handoff_id="handoff-001", envelope_id=envelope.envelope_id,
        claim_id=envelope.claim_id, consumption_id=envelope.consumption_id,
        authorization_id=envelope.authorization_id,
        execution_plan_fingerprint=envelope.execution_plan_fingerprint,
        authorization_decision_fingerprint=envelope.authorization_decision_fingerprint,
        stage63_claim_fingerprint=envelope.stage63_claim_fingerprint,
        stage64_envelope_request_fingerprint=envelope.envelope_request_fingerprint,
        stage64_envelope_fingerprint=envelope.envelope_fingerprint,
        selected_adapter_index=envelope.selected_adapter_index,
        requested_unit_count=1, runtime_boundary_id=boundary_id,
        runtime_boundary_kind="controlled_offline_acceptance_boundary",
        handoff_requested=True, caller_confirmation=True,
        scheduling_requested=False, execution_requested=False,
        provider_requested=False, translation_requested=False,
        handoff_scope=exact_handoff_scope(
            envelope_id=envelope.envelope_id,
            authorization_id=envelope.authorization_id,
            claim_id=envelope.claim_id,
            execution_plan_fingerprint=envelope.execution_plan_fingerprint,
            selected_adapter_index=envelope.selected_adapter_index,
            runtime_boundary_id=boundary_id,
        ),
        purpose="Stage 6.5 測試\r\nmetadata",
    )
    kwargs.update(request_overrides)
    request = ControlledRuntimeHandoffRequest(**kwargs)
    freeze = ControlledRuntimePreparationFreezeValidationResult(
        valid=True, frozen_file_count=16, public_api_count=41,
        invariant_count=49,
        activation_gate="controlled_runtime_preparation_frozen",
    )
    inputs = dict(
        request=request, freeze_validation=freeze, execution_plan=plan,
        authorization_request=auth_request,
        authorization_decision=auth_decision,
        authorization_result=auth_result, stage62_request=stage62_request,
        stage62_record=stage62_record, stage62_result=stage62_result,
        stage63_claim_request=stage63_claim_request,
        stage63_claim=stage63_claim, stage63_result=stage63_result,
        stage64_envelope_request=stage64_request,
        stage64_envelope=envelope, stage64_result=stage64_result,
    )
    return inputs


def accept(inputs=None):
    return ControlledRuntimeHandoffBoundary().accept(**(inputs or build_inputs()))


def test_authentic_envelope_is_accepted_without_scheduling_or_execution():
    result = accept()
    receipt = result.receipt
    assert result.status == "handoff_accepted_not_scheduled_not_executed"
    assert result.recommended_action == "retain_for_controlled_scheduling_authorization"
    assert result.runtime_boundary_invoked is True
    assert result.runtime_scheduled is result.runtime_invoked is False
    assert receipt.runtime_handoff_completed is True
    assert receipt.runtime_boundary_accepted is True
    assert receipt.runtime_execution_scheduled is False
    assert receipt.execution_started is receipt.execution_completed is False
    assert len(receipt.upstream_fingerprint_chain) == 17


def test_exact_bindings_and_one_unit_are_preserved():
    inputs = build_inputs()
    result = accept(inputs)
    receipt = result.receipt
    request = inputs["request"]
    assert receipt.envelope_id == request.envelope_id
    assert receipt.claim_id == request.claim_id
    assert receipt.authorization_id == request.authorization_id
    assert receipt.execution_plan_fingerprint == request.execution_plan_fingerprint
    assert receipt.selected_adapter_index == request.selected_adapter_index
    assert receipt.accepted_unit_count == 1
    assert receipt.runtime_boundary_id == request.runtime_boundary_id


def test_every_execution_write_and_activity_indicator_is_false():
    result = accept()
    receipt = result.receipt
    assert not any(getattr(receipt, name) for name in (
        "runtime_execution_scheduled", "execution_started", "execution_completed",
        "runtime_execution_enabled", "provider_execution_enabled",
        "network_execution_enabled", "translation_execution_enabled",
        "output_write_enabled", "resume_write_enabled", "cache_write_enabled",
        "retry_enabled", "fallback_enabled", "production_hook_enabled",
    ))
    assert not any(getattr(result, name) for name in (
        "runtime_scheduled", "runtime_invoked", "provider_invoked",
        "network_invoked", "translation_invoked", "output_written",
        "resume_written", "cache_written", "retry_used", "fallback_used",
        "production_hook_invoked",
    ))


def test_repeated_acceptance_is_deterministic_and_upstream_unchanged():
    inputs = build_inputs()
    snapshots = tuple(repr(value) for key, value in inputs.items() if key != "request")
    first = accept(inputs)
    second = accept(inputs)
    assert first.receipt == second.receipt
    assert first.result_fingerprint == second.result_fingerprint
    assert snapshots == tuple(
        repr(value) for key, value in inputs.items() if key != "request"
    )


def test_tampered_request_fingerprint_fails_closed():
    inputs = build_inputs()
    object.__setattr__(inputs["request"], "request_fingerprint", "0" * 64)
    result = accept(inputs)
    assert result.receipt is None
    assert result.status != "handoff_accepted_not_scheduled_not_executed"


def test_wrong_scope_fails_closed():
    inputs = build_inputs()
    object.__setattr__(inputs["request"], "handoff_scope", "broadened")
    object.__setattr__(
        inputs["request"], "request_fingerprint",
        __import__(
            "core.controlled_runtime_handoff_boundary.models",
            fromlist=["canonical_sha256"],
        ).canonical_sha256(inputs["request"]._fingerprint_payload()),
    )
    result = accept(inputs)
    assert result.status == "handoff_scope_mismatch"
    assert result.receipt is None


def test_invalid_upstream_states_fail_closed():
    cases = (
        ("freeze_validation", {"valid": False}),
        ("execution_plan", {"execution_started": True}),
        ("authorization_decision", {"authorization_reusable": True}),
        ("stage63_claim", {"execution_started": True}),
        ("stage64_envelope", {"runtime_handoff_completed": True}),
    )
    for key, changes in cases:
        inputs = build_inputs()
        inputs[key] = replace(inputs[key], **changes)
        result = accept(inputs)
        assert result.receipt is None, key


def test_boundary_state_is_immutable_and_has_no_capability_slots():
    boundary = ControlledRuntimeHandoffBoundary()
    for forbidden in ("scheduler", "executor", "provider", "queue", "worker", "registry"):
        assert not hasattr(boundary, forbidden)
    try:
        boundary._policy = None
    except AttributeError:
        pass
    else:
        raise AssertionError("boundary state was mutable")

def test_accept_has_zero_external_side_effects(monkeypatch):
    import asyncio
    import builtins
    import pathlib
    import socket
    import subprocess
    import threading

    from core.controlled_runtime_atomic_authorization_consumption.registry import (
        AtomicAuthorizationConsumptionRegistry,
    )

    inputs = build_inputs()

    def forbidden(*args, **kwargs):
        raise AssertionError("external side effect attempted")

    for name in ("claim", "read_claim", "count_claims"):
        monkeypatch.setattr(AtomicAuthorizationConsumptionRegistry, name, forbidden)
    monkeypatch.setattr(builtins, "open", forbidden)
    for name in ("open", "read_bytes", "read_text", "write_bytes", "write_text"):
        monkeypatch.setattr(pathlib.Path, name, forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(threading, "Thread", forbidden)
    monkeypatch.setattr(asyncio, "create_task", forbidden)

    result = accept(inputs)
    assert result.status == "handoff_accepted_not_scheduled_not_executed"
