from dataclasses import FrozenInstanceError, replace

import pytest

from core.controlled_runtime_queue_admission_record import (
    ControlledRuntimeQueueAdmissionRecordBuilder,
    QueueAdmissionRecordPreparationVerificationError,
    verify_controlled_runtime_queue_admission_record,
)
from core.controlled_runtime_queue_admission_record.policy import (
    PREPARATION_INTENT, SUCCESS_STATUS,
)
from tests.unit.controlled_runtime_queue_admission_record import build_context


def test_authentic_stage611_authority_produces_one_immutable_record(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmissionRecordBuilder().prepare(**context)
    record = result.record
    assert result.verification_succeeded and result.record_preparation_count == 1
    assert result.exactly_one_record_prepared
    assert record is not None and len(record.canonical_chain) == 31
    assert record.queue_admission_record_prepared
    assert not any((
        record.queue_admission_record_consumed,
        record.queue_record_created,
        record.runtime_execution_scheduled,
        record.execution_started,
    ))
    with pytest.raises(FrozenInstanceError):
        record.queue_admission_record_prepared = False


def test_repeated_preparation_is_deterministic_and_stateless(tmp_path):
    left_root, right_root = tmp_path / "left", tmp_path / "right"
    left_root.mkdir()
    right_root.mkdir()
    left = ControlledRuntimeQueueAdmissionRecordBuilder().prepare(**build_context(left_root))
    right = ControlledRuntimeQueueAdmissionRecordBuilder().prepare(**build_context(right_root))
    assert left == right


@pytest.mark.parametrize(
    "field",
    [
        "claim_fingerprint", "consumption_request_fingerprint",
        "decision_fingerprint", "authorization_request_fingerprint",
        "stage69_claim_fingerprint", "scheduling_envelope_fingerprint",
        "stage67_claim_fingerprint", "stage66_decision_fingerprint",
        "capability_state_fingerprint", "runtime_boundary_id",
        "selected_adapter_index",
    ],
)
def test_binding_tamper_is_denied(tmp_path, field):
    context = build_context(tmp_path)
    request = context["request"]
    value = getattr(request, field)
    object.__setattr__(
        request, field,
        value + 1 if isinstance(value, int) else (
            "0" * 64 if len(value) == 64 else value + "-tamper"
        ),
    )
    result = ControlledRuntimeQueueAdmissionRecordBuilder().prepare(**context)
    assert not result.verification_succeeded and result.record is None


@pytest.mark.parametrize("kind", ["missing", "extra", "duplicate", "reordered"])
def test_chain_tamper_is_rejected(tmp_path, kind):
    context = build_context(tmp_path)
    chain = list(context["request"].upstream_chain)
    if kind == "missing":
        chain.pop()
    elif kind == "extra":
        chain.append(chain[-1])
    elif kind == "duplicate":
        chain[1] = chain[0]
    else:
        chain[0], chain[1] = chain[1], chain[0]
    if len(chain) != 29:
        with pytest.raises(ValueError):
            replace(context["request"], upstream_chain=tuple(chain))
    else:
        context["request"] = replace(context["request"], upstream_chain=tuple(chain))
        result = ControlledRuntimeQueueAdmissionRecordBuilder().prepare(**context)
        assert not result.verification_succeeded


@pytest.mark.parametrize(
    "field,value",
    [
        ("verification_succeeded", False),
        ("upstream_verified", False),
        ("durable_claim_created", False),
        ("exactly_one_authorization_consumed", False),
        ("replay_detected", True),
        ("persistence_committed", False),
        ("durable_readback_verified", False),
    ],
)
def test_invalid_stage611_result_evidence_is_denied(tmp_path, field, value):
    context = build_context(tmp_path)
    context["stage611_result"] = replace(context["stage611_result"], **{field: value})
    result = ControlledRuntimeQueueAdmissionRecordBuilder().prepare(**context)
    assert not result.verification_succeeded


def test_exact_31_layer_chain(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmissionRecordBuilder().prepare(**context)
    record = result.record
    assert record is not None
    assert len(record.canonical_chain) == 31
    assert tuple(record.canonical_chain[:29]) == tuple(context["request"].upstream_chain)
    assert record.canonical_chain[29] == context["request"].request_fingerprint
    assert record.canonical_chain[30] == record.record_fingerprint


def test_counter_fields_are_zero(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmissionRecordBuilder().prepare(**context)
    assert (
        result.queue_admission_count,
        result.queue_record_created_count,
        result.queue_record_consumed_count,
        result.scheduling_queued_count,
        result.scheduler_count,
        result.runtime_execution_count,
        result.provider_execution_count,
        result.network_execution_count,
        result.translation_execution_count,
    ) == (0, 0, 0, 0, 0, 0, 0, 0, 0)


def test_verifier_raise_on_error(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmissionRecordBuilder().prepare(**context)
    bad = replace(result.record, queue_record_created=False)
    object.__setattr__(bad, "record_fingerprint", "0" * 64)
    with pytest.raises(QueueAdmissionRecordPreparationVerificationError):
        verify_controlled_runtime_queue_admission_record(
            bad, request=context["request"],
            stage611_claim=context["stage611_claim"],
            stage611_request=context["stage611_request"],
            stage611_result=context["stage611_result"],
            stage611_verification_context=context["stage611_verification_context"],
            raise_on_error=True,
        )
