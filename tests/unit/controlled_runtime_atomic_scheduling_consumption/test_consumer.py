from dataclasses import replace

import pytest

from core.controlled_runtime_atomic_scheduling_consumption import (
    AtomicSchedulingAuthorizationConsumer,
    AtomicSchedulingAuthorizationConsumptionRegistry,
)
from . import build_context


def consume(context):
    return AtomicSchedulingAuthorizationConsumer().consume(**context)


def test_authentic_stage66_decision_is_consumed_once_without_scheduling(tmp_path):
    context = build_context(tmp_path)
    before = tuple(repr(value) for value in context.values())
    result = consume(context)
    assert result.status == "scheduling_authorization_consumed_not_scheduled"
    assert result.recommended_action == "retain_for_controlled_runtime_scheduling_envelope"
    assert result.consumer_invoked is True
    assert result.registry_read is True
    assert result.registry_written is True
    assert result.claim is not None
    claim = result.claim
    assert claim.scheduling_authorization_consumed is True
    assert claim.scheduling_authorization_reusable is False
    assert claim.durable_scheduling_reuse_prevention_established is True
    assert claim.persistent_scheduling_registry_written is True
    assert claim.authorization_consumed is True
    assert claim.authorization_reusable is False
    assert claim.runtime_handoff_completed is True
    assert claim.runtime_boundary_accepted is True
    assert claim.consumed_schedule_unit_count == 1
    assert len(claim.upstream_fingerprint_chain) == 21
    assert before == tuple(repr(value) for value in context.values())


def test_all_scheduling_execution_and_write_activity_remains_false(tmp_path):
    result = consume(build_context(tmp_path))
    claim = result.claim
    assert claim is not None
    assert not any(getattr(claim, name) for name in (
        "runtime_execution_scheduled", "queue_record_created",
        "job_record_created", "worker_started", "execution_started",
        "execution_completed", "runtime_execution_enabled",
        "provider_execution_enabled", "network_execution_enabled",
        "translation_execution_enabled", "output_write_enabled",
        "resume_write_enabled", "cache_write_enabled", "retry_enabled",
        "fallback_enabled", "production_hook_enabled",
    ))
    assert not any(getattr(result, name) for name in (
        "scheduler_invoked", "queue_written", "job_created", "worker_started",
        "runtime_invoked", "provider_invoked", "network_invoked",
        "translation_invoked", "output_written", "resume_written",
        "cache_written", "retry_used", "fallback_used",
        "production_hook_invoked",
    ))


def test_exact_bindings_and_complete_chain_are_preserved(tmp_path):
    context = build_context(tmp_path)
    result = consume(context)
    claim = result.claim
    decision = context["stage66_scheduling_decision"]
    request = context["request"]
    assert claim.execution_plan_fingerprint == decision.execution_plan_fingerprint
    assert claim.execution_authorization_decision_fingerprint == decision.execution_authorization_decision_fingerprint
    assert claim.stage63_claim_fingerprint == decision.stage63_claim_fingerprint
    assert claim.stage64_envelope_fingerprint == decision.stage64_envelope_fingerprint
    assert claim.stage65_handoff_receipt_fingerprint == decision.stage65_handoff_receipt_fingerprint
    assert claim.stage66_scheduling_decision_fingerprint == decision.decision_fingerprint
    assert claim.selected_adapter_index == decision.selected_adapter_index
    assert claim.runtime_boundary_id == decision.runtime_boundary_id
    assert claim.upstream_fingerprint_chain[:19] == decision.upstream_fingerprint_chain
    assert claim.upstream_fingerprint_chain[19] == request.request_fingerprint
    assert claim.upstream_fingerprint_chain[20] == claim.claim_fingerprint


def test_replay_and_new_consumption_id_are_fail_closed(tmp_path):
    context = build_context(tmp_path)
    first = consume(context)
    second = consume(context)
    third = consume(build_context(tmp_path, scheduling_consumption_id="schedule-consume-002"))
    assert first.claim is not None
    assert second.status == third.status == "already_consumed"
    assert AtomicSchedulingAuthorizationConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    ).count_claims() == 1


def test_raw_request_fingerprint_tampering_fails_before_registry(tmp_path):
    context = build_context(tmp_path)
    object.__setattr__(context["request"], "request_fingerprint", "0" * 64)
    result = consume(context)
    assert result.claim is None
    assert result.status == "consumption_scope_mismatch"
    assert not context["database_path"].exists()


@pytest.mark.parametrize("field,value", (
    ("scheduling_authorization_id", "other"),
    ("handoff_id", "other"),
    ("envelope_id", "other"),
    ("claim_id", "other"),
    ("consumption_id", "other"),
    ("authorization_id", "other"),
    ("execution_plan_fingerprint", "0" * 64),
    ("execution_authorization_decision_fingerprint", "0" * 64),
    ("stage63_claim_fingerprint", "0" * 64),
    ("stage64_envelope_fingerprint", "0" * 64),
    ("stage65_handoff_receipt_fingerprint", "0" * 64),
    ("stage66_scheduling_request_fingerprint", "0" * 64),
    ("stage66_scheduling_decision_fingerprint", "0" * 64),
    ("selected_adapter_index", 1),
    ("runtime_boundary_id", "other"),
))
def test_request_binding_mismatches_fail_closed(tmp_path, field, value):
    result = consume(build_context(tmp_path, **{field: value}))
    assert result.claim is None
    assert result.status != "scheduling_authorization_consumed_not_scheduled"


@pytest.mark.parametrize("key,changes", (
    ("freeze_validation", {"valid": False}),
    ("execution_plan", {"execution_started": True}),
    ("execution_plan", {"execution_completed": True}),
    ("execution_plan", {"provider_requests_executed": 1}),
    ("authorization_decision", {"authorized": False}),
    ("authorization_decision", {"authorization_reusable": True}),
    ("stage62_record", {"authorization_reusable": True}),
    ("stage63_claim", {"authorization_consumed": False}),
    ("stage63_claim", {"execution_started": True}),
    ("stage64_envelope", {"runtime_execution_enabled": True}),
    ("stage65_handoff_receipt", {"runtime_handoff_completed": False}),
    ("stage65_handoff_receipt", {"runtime_boundary_accepted": False}),
    ("stage66_scheduling_decision", {"scheduling_authorized": False}),
    ("stage66_scheduling_decision", {"scheduling_authorization_consumed": True}),
    ("stage66_scheduling_decision", {"scheduling_authorization_reusable": True}),
    ("stage66_scheduling_decision", {"schedule_once": False}),
    ("stage66_scheduling_decision", {"runtime_execution_scheduled": True}),
    ("stage66_scheduling_decision", {"queue_record_created": True}),
    ("stage66_scheduling_decision", {"job_record_created": True}),
    ("stage66_scheduling_decision", {"worker_started": True}),
    ("stage66_scheduling_decision", {"execution_started": True}),
    ("stage66_scheduling_decision", {"execution_completed": True}),
    ("stage66_scheduling_decision", {"runtime_execution_enabled": True}),
    ("stage66_scheduling_decision", {"provider_execution_enabled": True}),
    ("stage66_scheduling_decision", {"network_execution_enabled": True}),
    ("stage66_scheduling_decision", {"translation_execution_enabled": True}),
    ("stage66_scheduling_decision", {"output_write_enabled": True}),
    ("stage66_scheduling_decision", {"resume_write_enabled": True}),
    ("stage66_scheduling_decision", {"cache_write_enabled": True}),
    ("stage66_scheduling_decision", {"retry_enabled": True}),
    ("stage66_scheduling_decision", {"fallback_enabled": True}),
    ("stage66_scheduling_decision", {"production_hook_enabled": True}),
))
def test_ineligible_upstream_contracts_fail_closed(tmp_path, key, changes):
    context = build_context(tmp_path)
    context[key] = replace(context[key], **changes)
    result = consume(context)
    assert result.claim is None
    assert result.status != "scheduling_authorization_consumed_not_scheduled"


def test_consumer_has_no_external_capability_state():
    consumer = AtomicSchedulingAuthorizationConsumer()
    for forbidden in (
        "scheduler", "queue", "job_store", "worker", "runtime", "provider",
        "network", "executor", "stage63_registry",
    ):
        assert not hasattr(consumer, forbidden)
    with pytest.raises(AttributeError):
        consumer._policy = None


def test_consumer_starts_no_thread_subprocess_async_task_or_stage63_access(tmp_path, monkeypatch):
    import asyncio
    import socket
    import subprocess
    import threading
    from core.controlled_runtime_atomic_authorization_consumption.registry import (
        AtomicAuthorizationConsumptionRegistry,
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("forbidden side effect attempted")

    for name in ("claim", "read_claim", "count_claims"):
        monkeypatch.setattr(AtomicAuthorizationConsumptionRegistry, name, forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(threading, "Thread", forbidden)
    monkeypatch.setattr(asyncio, "create_task", forbidden)
    assert consume(build_context(tmp_path)).claim is not None