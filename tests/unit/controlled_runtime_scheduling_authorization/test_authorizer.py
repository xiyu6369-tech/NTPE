from dataclasses import replace

import pytest

from core.controlled_runtime_handoff_boundary import ControlledRuntimeHandoffBoundary
from core.controlled_runtime_scheduling_authorization import (
    ControlledRuntimeSchedulingAuthorizationRequest,
    ControlledRuntimeSchedulingAuthorizer,
)
from core.controlled_runtime_scheduling_authorization.policy import (
    exact_scheduling_scope,
)
from tests.unit.controlled_runtime_handoff_boundary.test_boundary import (
    build_inputs as build_stage65_inputs,
)


def build_inputs(**request_overrides):
    upstream = build_stage65_inputs()
    stage65_result = ControlledRuntimeHandoffBoundary().accept(**upstream)
    receipt = stage65_result.receipt
    assert receipt is not None
    kwargs = dict(
        scheduling_authorization_id="schedule-auth-001",
        handoff_id=receipt.handoff_id,
        envelope_id=receipt.envelope_id,
        claim_id=receipt.claim_id,
        consumption_id=receipt.consumption_id,
        authorization_id=receipt.authorization_id,
        execution_plan_fingerprint=receipt.execution_plan_fingerprint,
        execution_authorization_decision_fingerprint=
            receipt.authorization_decision_fingerprint,
        stage63_claim_fingerprint=receipt.stage63_claim_fingerprint,
        stage64_envelope_fingerprint=receipt.stage64_envelope_fingerprint,
        stage65_handoff_request_fingerprint=
            stage65_result.request.request_fingerprint,
        stage65_handoff_receipt_fingerprint=receipt.receipt_fingerprint,
        selected_adapter_index=receipt.selected_adapter_index,
        requested_schedule_unit_count=1,
        runtime_boundary_id=receipt.runtime_boundary_id,
        runtime_boundary_kind=receipt.runtime_boundary_kind,
        scheduling_authorization_requested=True,
        schedule_once=True,
        caller_confirmation=True,
        queue_creation_requested=False,
        job_creation_requested=False,
        worker_start_requested=False,
        runtime_execution_requested=False,
        provider_execution_requested=False,
        translation_execution_requested=False,
        scheduling_scope="pending",
        purpose="Stage 6.6 測試\r\nmetadata",
    )
    kwargs["scheduling_scope"] = exact_scheduling_scope(
        handoff_id=kwargs["handoff_id"], envelope_id=kwargs["envelope_id"],
        claim_id=kwargs["claim_id"],
        consumption_id=kwargs["consumption_id"],
        authorization_id=kwargs["authorization_id"],
        execution_plan_fingerprint=kwargs["execution_plan_fingerprint"],
        execution_authorization_decision_fingerprint=
            kwargs["execution_authorization_decision_fingerprint"],
        stage63_claim_fingerprint=kwargs["stage63_claim_fingerprint"],
        stage64_envelope_fingerprint=kwargs["stage64_envelope_fingerprint"],
        stage65_handoff_receipt_fingerprint=
            kwargs["stage65_handoff_receipt_fingerprint"],
        selected_adapter_index=kwargs["selected_adapter_index"],
        runtime_boundary_id=kwargs["runtime_boundary_id"],
    )
    kwargs.update(request_overrides)
    request = ControlledRuntimeSchedulingAuthorizationRequest(**kwargs)
    return dict(
        request=request,
        freeze_validation=upstream["freeze_validation"],
        execution_plan=upstream["execution_plan"],
        authorization_request=upstream["authorization_request"],
        authorization_decision=upstream["authorization_decision"],
        authorization_result=upstream["authorization_result"],
        stage62_request=upstream["stage62_request"],
        stage62_record=upstream["stage62_record"],
        stage62_result=upstream["stage62_result"],
        stage63_claim_request=upstream["stage63_claim_request"],
        stage63_claim=upstream["stage63_claim"],
        stage63_result=upstream["stage63_result"],
        stage64_envelope_request=upstream["stage64_envelope_request"],
        stage64_envelope=upstream["stage64_envelope"],
        stage64_result=upstream["stage64_result"],
        stage65_handoff_request=stage65_result.request,
        stage65_handoff_receipt=receipt,
        stage65_result=stage65_result,
    )


def authorize(inputs=None):
    return ControlledRuntimeSchedulingAuthorizer().authorize(
        **(inputs or build_inputs())
    )


def test_authentic_handoff_is_authorized_without_scheduling():
    result = authorize()
    decision = result.decision
    assert result.status == "scheduling_authorized_not_consumed_not_scheduled"
    assert (
        result.recommended_action
        == "retain_for_atomic_scheduling_authorization_consumption"
    )
    assert result.authorizer_invoked is True
    assert decision.scheduling_authorization_requested is True
    assert decision.scheduling_authorized is True
    assert decision.scheduling_authorization_consumed is False
    assert decision.scheduling_authorization_reusable is False
    assert decision.schedule_once is True


def test_upstream_consumption_handoff_and_exact_bindings_preserved():
    inputs = build_inputs()
    decision = authorize(inputs).decision
    receipt = inputs["stage65_handoff_receipt"]
    assert decision.authorization_consumed is True
    assert decision.authorization_reusable is False
    assert decision.durable_reuse_prevention_established is True
    assert decision.persistent_registry_written is True
    assert decision.runtime_handoff_prepared is True
    assert decision.runtime_handoff_completed is True
    assert decision.runtime_boundary_accepted is True
    assert decision.execution_plan_fingerprint == receipt.execution_plan_fingerprint
    assert decision.stage63_claim_fingerprint == receipt.stage63_claim_fingerprint
    assert (
        decision.stage64_envelope_fingerprint
        == receipt.stage64_envelope_fingerprint
    )
    assert (
        decision.stage65_handoff_receipt_fingerprint
        == receipt.receipt_fingerprint
    )
    assert decision.selected_adapter_index == receipt.selected_adapter_index
    assert decision.authorized_schedule_unit_count == 1
    assert decision.runtime_boundary_id == receipt.runtime_boundary_id


def test_all_scheduling_execution_and_write_activity_remains_false():
    result = authorize()
    decision = result.decision
    assert not any(getattr(decision, name) for name in (
        "scheduling_authorization_consumed", "runtime_execution_scheduled",
        "queue_record_created", "job_record_created", "worker_started",
        "execution_started", "execution_completed",
        "runtime_execution_enabled", "provider_execution_enabled",
        "network_execution_enabled", "translation_execution_enabled",
        "output_write_enabled", "resume_write_enabled", "cache_write_enabled",
        "retry_enabled", "fallback_enabled", "production_hook_enabled",
    ))
    assert not any(getattr(result, name) for name in (
        "scheduler_invoked", "queue_written", "job_created", "worker_started",
        "runtime_invoked", "provider_invoked", "network_invoked",
        "translation_invoked", "output_written", "resume_written",
        "cache_written", "retry_used", "fallback_used",
        "production_hook_invoked",
    ))


def test_complete_nineteen_layer_chain_and_determinism():
    inputs = build_inputs()
    snapshots = tuple(repr(value) for value in inputs.values())
    first = authorize(inputs)
    second = authorize(inputs)
    assert first == second
    assert len(first.decision.upstream_fingerprint_chain) == 19
    assert (
        first.decision.upstream_fingerprint_chain[:17]
        == inputs["stage65_handoff_receipt"].upstream_fingerprint_chain
    )
    assert first.decision.upstream_fingerprint_chain[17] == (
        inputs["request"].request_fingerprint
    )
    assert first.decision.upstream_fingerprint_chain[18] == (
        first.decision.decision_fingerprint
    )
    assert snapshots == tuple(repr(value) for value in inputs.values())


@pytest.mark.parametrize("key,changes", (
    ("freeze_validation", {"valid": False}),
    ("execution_plan", {"execution_started": True}),
    ("execution_plan", {"provider_requests_executed": 1}),
    ("authorization_decision", {"authorized": False}),
    ("authorization_decision", {"authorization_reusable": True}),
    ("stage62_record", {"authorization_reusable": True}),
    ("stage63_claim", {"authorization_consumed": False}),
    ("stage63_claim", {"execution_started": True}),
    ("stage64_envelope", {"runtime_execution_enabled": True}),
    ("stage65_handoff_receipt", {"runtime_handoff_completed": False}),
    ("stage65_handoff_receipt", {"runtime_boundary_accepted": False}),
    ("stage65_handoff_receipt", {"runtime_execution_scheduled": True}),
    ("stage65_handoff_receipt", {"execution_started": True}),
    ("stage65_handoff_receipt", {"execution_completed": True}),
    ("stage65_handoff_receipt", {"provider_execution_enabled": True}),
    ("stage65_handoff_receipt", {"network_execution_enabled": True}),
    ("stage65_handoff_receipt", {"translation_execution_enabled": True}),
    ("stage65_handoff_receipt", {"output_write_enabled": True}),
    ("stage65_handoff_receipt", {"resume_write_enabled": True}),
    ("stage65_handoff_receipt", {"cache_write_enabled": True}),
    ("stage65_handoff_receipt", {"retry_enabled": True}),
    ("stage65_handoff_receipt", {"fallback_enabled": True}),
    ("stage65_handoff_receipt", {"production_hook_enabled": True}),
))
def test_invalid_upstream_contracts_fail_closed(key, changes):
    inputs = build_inputs()
    inputs[key] = replace(inputs[key], **changes)
    result = authorize(inputs)
    assert result.decision is None
    assert result.status != "scheduling_authorized_not_consumed_not_scheduled"


@pytest.mark.parametrize("field,value", (
    ("handoff_id", "other"),
    ("envelope_id", "other"),
    ("claim_id", "other"),
    ("consumption_id", "other"),
    ("authorization_id", "other"),
    ("execution_plan_fingerprint", "0" * 64),
    ("execution_authorization_decision_fingerprint", "0" * 64),
    ("stage63_claim_fingerprint", "0" * 64),
    ("stage64_envelope_fingerprint", "0" * 64),
    ("stage65_handoff_request_fingerprint", "0" * 64),
    ("stage65_handoff_receipt_fingerprint", "0" * 64),
    ("selected_adapter_index", 1),
    ("runtime_boundary_id", "other"),
))
def test_request_binding_mismatches_fail_closed(field, value):
    inputs = build_inputs(**{field: value})
    result = authorize(inputs)
    assert result.decision is None


def test_broadened_scope_and_raw_fingerprint_tampering_fail_closed():
    inputs = build_inputs(scheduling_scope="broadened")
    assert authorize(inputs).status == "scheduling_scope_mismatch"
    inputs = build_inputs()
    object.__setattr__(inputs["request"], "request_fingerprint", "0" * 64)
    assert authorize(inputs).decision is None


def test_authorizer_has_no_external_capability_state():
    authorizer = ControlledRuntimeSchedulingAuthorizer()
    for forbidden in (
        "scheduler", "queue", "job_store", "worker", "runtime", "provider",
        "network", "registry", "executor",
    ):
        assert not hasattr(authorizer, forbidden)
    with pytest.raises(AttributeError):
        authorizer._policy = None


def test_authorize_has_zero_external_side_effects(monkeypatch):
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
    assert authorize(inputs).decision is not None
