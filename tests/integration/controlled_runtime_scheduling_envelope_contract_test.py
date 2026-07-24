from core.controlled_runtime_scheduling_envelope import (
    ControlledRuntimeSchedulingEnvelopeBuilder,
    verify_controlled_runtime_scheduling_envelope,
)
from tests.unit.controlled_runtime_scheduling_envelope import build_context


def test_complete_authentic_stage53_through_stage68_contract(tmp_path):
    context = build_context(tmp_path)
    before = tuple(repr(value) for value in context.values())
    result = ControlledRuntimeSchedulingEnvelopeBuilder().build(**context)
    after = tuple(repr(value) for value in context.values())
    envelope = result.scheduling_envelope
    assert before == after
    assert result.status == (
        "scheduling_envelope_prepared_not_admitted_not_scheduled"
    )
    assert envelope is not None
    assert len(envelope.upstream_fingerprint_chain) == 23
    assert envelope.upstream_fingerprint_chain[:21] == (
        context[
            "stage67_scheduling_consumption_claim"
        ].upstream_fingerprint_chain
    )
    verification = verify_controlled_runtime_scheduling_envelope(
        envelope,
        request=context["request"],
        stage67_scheduling_consumption_request=
            context["stage67_scheduling_consumption_request"],
        stage67_scheduling_consumption_claim=
            context["stage67_scheduling_consumption_claim"],
        stage66_scheduling_decision=
            context["stage66_scheduling_decision"],
        stage65_handoff_receipt=context["stage65_handoff_receipt"],
        stage64_envelope=context["stage64_envelope"],
        stage63_claim=context["stage63_claim"],
        stage62_record=context["stage62_record"],
        authorization_decision=context["authorization_decision"],
        execution_plan=context["execution_plan"],
    )
    assert verification.valid


def test_envelope_preparation_does_not_admit_schedule_or_execute(tmp_path):
    result = ControlledRuntimeSchedulingEnvelopeBuilder().build(
        **build_context(tmp_path)
    )
    envelope = result.scheduling_envelope
    assert envelope.scheduling_envelope_prepared is True
    assert envelope.queue_admission_authorized is False
    assert envelope.runtime_execution_scheduled is False
    assert envelope.queue_record_created is False
    assert envelope.job_record_created is False
    assert envelope.worker_started is False
    assert envelope.execution_started is False
    assert envelope.execution_completed is False
    assert result.queue_admission_invoked is False
    assert result.scheduler_invoked is False
    assert result.queue_written is False
    assert result.runtime_invoked is False


def test_complete_integration_is_deterministic(tmp_path):
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    left_root.mkdir()
    right_root.mkdir()
    left = ControlledRuntimeSchedulingEnvelopeBuilder().build(
        **build_context(left_root)
    )
    right = ControlledRuntimeSchedulingEnvelopeBuilder().build(
        **build_context(right_root)
    )
    assert left == right
