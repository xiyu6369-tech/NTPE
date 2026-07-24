import pytest

from core.controlled_runtime_scheduling_envelope import (
    ControlledRuntimeSchedulingEnvelopeBuilder,
)
from . import build_context


def build(context):
    return ControlledRuntimeSchedulingEnvelopeBuilder().build(**context)


def test_authentic_stage67_claim_builds_one_envelope_without_admission(tmp_path):
    context = build_context(tmp_path)
    before = tuple(repr(value) for value in context.values())
    result = build(context)
    after = tuple(repr(value) for value in context.values())
    envelope = result.scheduling_envelope
    assert before == after
    assert result.status == (
        "scheduling_envelope_prepared_not_admitted_not_scheduled"
    )
    assert result.recommended_action == (
        "retain_for_controlled_queue_admission_authorization"
    )
    assert result.builder_invoked is True
    assert envelope is not None
    assert envelope.scheduling_envelope_prepared is True
    assert envelope.scheduling_envelope_consumed is False
    assert envelope.scheduling_envelope_reusable is False
    assert envelope.queue_admission_authorized is False


def test_consumed_authorization_and_exact_bindings_are_preserved(tmp_path):
    context = build_context(tmp_path)
    result = build(context)
    envelope = result.scheduling_envelope
    claim = context["stage67_scheduling_consumption_claim"]
    assert envelope.authorization_consumed is True
    assert envelope.authorization_reusable is False
    assert envelope.scheduling_authorization_consumed is True
    assert envelope.scheduling_authorization_reusable is False
    assert envelope.durable_scheduling_reuse_prevention_established is True
    assert envelope.persistent_scheduling_registry_written is True
    assert envelope.execution_plan_fingerprint == claim.execution_plan_fingerprint
    assert (
        envelope.execution_authorization_decision_fingerprint
        == claim.execution_authorization_decision_fingerprint
    )
    assert envelope.stage63_claim_fingerprint == claim.stage63_claim_fingerprint
    assert (
        envelope.stage64_envelope_fingerprint
        == claim.stage64_envelope_fingerprint
    )
    assert (
        envelope.stage65_handoff_receipt_fingerprint
        == claim.stage65_handoff_receipt_fingerprint
    )
    assert (
        envelope.stage66_scheduling_decision_fingerprint
        == claim.stage66_scheduling_decision_fingerprint
    )
    assert (
        envelope.stage67_scheduling_consumption_claim_fingerprint
        == claim.claim_fingerprint
    )
    assert envelope.selected_adapter_index == claim.selected_adapter_index
    assert envelope.schedule_unit_count == 1
    assert envelope.runtime_boundary_id == claim.runtime_boundary_id


def test_complete_twenty_three_layer_chain_and_determinism(tmp_path):
    context = build_context(tmp_path)
    first = build(context)
    second = build(context)
    assert first == second
    envelope = first.scheduling_envelope
    claim = context["stage67_scheduling_consumption_claim"]
    assert len(envelope.upstream_fingerprint_chain) == 23
    assert envelope.upstream_fingerprint_chain[:21] == (
        claim.upstream_fingerprint_chain
    )
    assert envelope.upstream_fingerprint_chain[21] == (
        context["request"].request_fingerprint
    )
    assert envelope.upstream_fingerprint_chain[22] == (
        envelope.scheduling_envelope_fingerprint
    )


def test_all_activity_indicators_remain_false(tmp_path):
    result = build(build_context(tmp_path))
    envelope = result.scheduling_envelope
    assert not any(
        getattr(envelope, name)
        for name in (
            "scheduling_envelope_consumed",
            "queue_admission_authorized",
            "runtime_execution_scheduled",
            "queue_record_created",
            "job_record_created",
            "worker_started",
            "execution_started",
            "execution_completed",
            "runtime_execution_enabled",
            "provider_execution_enabled",
            "network_execution_enabled",
            "translation_execution_enabled",
            "output_write_enabled",
            "resume_write_enabled",
            "cache_write_enabled",
            "retry_enabled",
            "fallback_enabled",
            "production_hook_enabled",
        )
    )
    assert not any(
        getattr(result, name)
        for name in (
            "stage67_registry_read",
            "stage67_registry_written",
            "scheduler_invoked",
            "queue_admission_invoked",
            "queue_written",
            "job_created",
            "worker_started",
            "runtime_invoked",
            "provider_invoked",
            "network_invoked",
            "translation_invoked",
            "output_written",
            "resume_written",
            "cache_written",
            "retry_used",
            "fallback_used",
            "production_hook_invoked",
        )
    )


def test_raw_request_fingerprint_and_broadened_scope_fail_closed(tmp_path):
    context = build_context(tmp_path)
    object.__setattr__(context["request"], "request_fingerprint", "0" * 64)
    assert build(context).scheduling_envelope is None
    other = tmp_path / "other"
    other.mkdir()
    broadened = build_context(other, scheduling_scope="broadened")
    assert build(broadened).status == "scheduling_scope_mismatch"


@pytest.mark.parametrize(
    "field,value",
    (
        ("scheduling_consumption_id", "other"),
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
        ("stage67_scheduling_consumption_request_fingerprint", "0" * 64),
        ("stage67_scheduling_consumption_claim_fingerprint", "0" * 64),
        ("selected_adapter_index", 1),
        ("runtime_boundary_id", "other"),
    ),
)
def test_request_binding_mismatches_fail_closed(tmp_path, field, value):
    result = build(build_context(tmp_path, **{field: value}))
    assert result.scheduling_envelope is None
    assert result.status != (
        "scheduling_envelope_prepared_not_admitted_not_scheduled"
    )


@pytest.mark.parametrize(
    "key,field,value",
    (
        ("freeze_validation", "valid", False),
        ("execution_plan", "execution_started", True),
        ("execution_plan", "execution_completed", True),
        ("execution_plan", "provider_requests_executed", 1),
        ("authorization_decision", "authorization_reusable", True),
        ("stage62_record", "authorization_reusable", True),
        ("stage63_claim", "authorization_consumed", False),
        ("stage63_claim", "execution_started", True),
        ("stage64_envelope", "runtime_execution_enabled", True),
        ("stage65_handoff_receipt", "runtime_handoff_completed", False),
        ("stage66_scheduling_decision", "scheduling_authorized", False),
        (
            "stage67_scheduling_consumption_claim",
            "scheduling_authorization_consumed",
            False,
        ),
        (
            "stage67_scheduling_consumption_claim",
            "scheduling_authorization_reusable",
            True,
        ),
        (
            "stage67_scheduling_consumption_claim",
            "durable_scheduling_reuse_prevention_established",
            False,
        ),
        (
            "stage67_scheduling_consumption_claim",
            "persistent_scheduling_registry_written",
            False,
        ),
        (
            "stage67_scheduling_consumption_claim",
            "runtime_execution_scheduled",
            True,
        ),
        (
            "stage67_scheduling_consumption_claim",
            "queue_record_created",
            True,
        ),
        ("stage67_scheduling_consumption_claim", "job_record_created", True),
        ("stage67_scheduling_consumption_claim", "worker_started", True),
        ("stage67_scheduling_consumption_claim", "execution_started", True),
        ("stage67_scheduling_consumption_claim", "execution_completed", True),
        (
            "stage67_scheduling_consumption_claim",
            "runtime_execution_enabled",
            True,
        ),
        (
            "stage67_scheduling_consumption_claim",
            "provider_execution_enabled",
            True,
        ),
        (
            "stage67_scheduling_consumption_claim",
            "network_execution_enabled",
            True,
        ),
        (
            "stage67_scheduling_consumption_claim",
            "translation_execution_enabled",
            True,
        ),
        (
            "stage67_scheduling_consumption_claim",
            "output_write_enabled",
            True,
        ),
        (
            "stage67_scheduling_consumption_claim",
            "resume_write_enabled",
            True,
        ),
        (
            "stage67_scheduling_consumption_claim",
            "cache_write_enabled",
            True,
        ),
        ("stage67_scheduling_consumption_claim", "retry_enabled", True),
        ("stage67_scheduling_consumption_claim", "fallback_enabled", True),
        (
            "stage67_scheduling_consumption_claim",
            "production_hook_enabled",
            True,
        ),
    ),
)
def test_invalid_upstream_contracts_fail_closed(tmp_path, key, field, value):
    context = build_context(tmp_path)
    object.__setattr__(context[key], field, value)
    result = build(context)
    assert result.scheduling_envelope is None


def test_builder_has_no_external_capability_state():
    builder = ControlledRuntimeSchedulingEnvelopeBuilder()
    for name in (
        "registry",
        "scheduler",
        "queue_admission",
        "queue",
        "job_store",
        "worker",
        "runtime",
        "provider",
        "network",
        "executor",
    ):
        assert not hasattr(builder, name)
    with pytest.raises(AttributeError):
        builder._policy = None


def test_builder_does_not_access_registry_or_start_external_activity(
    tmp_path,
    monkeypatch,
):
    import asyncio
    import socket
    import subprocess
    import threading
    from core.controlled_runtime_atomic_scheduling_consumption.registry import (
        AtomicSchedulingAuthorizationConsumptionRegistry,
    )

    context = build_context(tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("forbidden Stage 6.8 side effect")

    for name in ("claim", "read", "count_claims"):
        monkeypatch.setattr(
            AtomicSchedulingAuthorizationConsumptionRegistry,
            name,
            forbidden,
        )
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(threading, "Thread", forbidden)
    monkeypatch.setattr(asyncio, "create_task", forbidden)
    assert build(context).scheduling_envelope is not None
