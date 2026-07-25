import sqlite3
from dataclasses import FrozenInstanceError, replace

import pytest

from core.controlled_runtime_queue_admission_record_consumption import (
    ControlledRuntimeQueueAdmissionRecordConsumer,
    ControlledRuntimeQueueAdmissionRecordConsumptionRegistry,
    QueueAdmissionRecordConsumptionIntegrityError,
    QueueAdmissionRecordConsumptionPathError,
    QueueAdmissionRecordConsumptionSchemaError,
    QueueAdmissionRecordConsumptionVerificationError,
    verify_controlled_runtime_queue_admission_record_consumption,
)
from core.controlled_runtime_queue_admission_record_consumption.registry import TABLE
from tests.unit.controlled_runtime_queue_admission_record_consumption import (
    build_context,
)


def test_first_consumption_succeeds_and_replay_is_closed(tmp_path):
    context = build_context(tmp_path)
    consumer = ControlledRuntimeQueueAdmissionRecordConsumer()
    first = consumer.consume(**context)
    second = consumer.consume(**context)
    claim = first.claim

    assert first.verification_succeeded
    assert first.exactly_one_record_consumed
    assert first.record_consumption_count == 1
    assert claim is not None
    assert len(claim.canonical_chain) == 33
    assert tuple(claim.canonical_chain[:31]) == tuple(
        context["stage612_record"].canonical_chain
    )
    assert claim.canonical_chain[31] == context["request"].request_fingerprint
    assert claim.canonical_chain[32] == claim.claim_fingerprint
    assert claim.queue_admission_record_consumed
    assert not claim.queue_admission_record_reusable
    assert second.replay_detected
    assert second.claim is None
    assert second.record_consumption_count == 0

    registry = ControlledRuntimeQueueAdmissionRecordConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert registry.count_claims() == 1
    assert registry.read(context["request"].consumption_request_id) == claim
    with pytest.raises(FrozenInstanceError):
        claim.queue_admission_record_consumed = False


@pytest.mark.parametrize(
    "field",
    [
        "record_fingerprint",
        "record_request_fingerprint",
        "claim_fingerprint",
        "consumption_request_fingerprint",
        "decision_fingerprint",
        "authorization_request_fingerprint",
        "stage69_claim_fingerprint",
        "scheduling_envelope_fingerprint",
        "stage67_claim_fingerprint",
        "stage66_decision_fingerprint",
        "capability_state_fingerprint",
        "runtime_boundary_id",
        "selected_adapter_index",
        "ordering_key",
    ],
)
def test_request_binding_tamper_is_denied(tmp_path, field):
    context = build_context(tmp_path)
    value = getattr(context["request"], field)
    object.__setattr__(
        context["request"],
        field,
        value + 1
        if isinstance(value, int)
        else ("0" * 64 if len(value) == 64 else value + "-tamper"),
    )
    result = ControlledRuntimeQueueAdmissionRecordConsumer().consume(**context)
    assert not result.verification_succeeded
    assert result.claim is None
    assert result.record_consumption_count == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("verification_succeeded", False),
        ("upstream_verified", False),
        ("exactly_one_record_prepared", False),
        ("replay_detected", True),
    ],
)
def test_invalid_stage612_result_evidence_is_denied(tmp_path, field, value):
    context = build_context(tmp_path)
    context["stage612_result"] = replace(
        context["stage612_result"], **{field: value}
    )
    result = ControlledRuntimeQueueAdmissionRecordConsumer().consume(**context)
    assert not result.verification_succeeded
    assert result.claim is None


def test_result_and_claim_keep_all_active_capabilities_zero(tmp_path):
    result = ControlledRuntimeQueueAdmissionRecordConsumer().consume(
        **build_context(tmp_path)
    )
    claim = result.claim
    assert claim is not None
    assert not any(
        (
            claim.queue_record_created,
            claim.runtime_execution_scheduled,
            claim.execution_started,
        )
    )
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


def test_transaction_rolls_back_on_injected_failure(tmp_path, monkeypatch):
    context = build_context(tmp_path)

    def fail(point):
        if point == "after_insert":
            raise RuntimeError("injected")

    injected = ControlledRuntimeQueueAdmissionRecordConsumptionRegistry(
        context["database_path"],
        allowed_root=tmp_path,
        failure_injector=fail,
    )
    original = ControlledRuntimeQueueAdmissionRecordConsumptionRegistry.claim
    monkeypatch.setattr(
        ControlledRuntimeQueueAdmissionRecordConsumptionRegistry,
        "claim",
        lambda self, request, claim: original(injected, request, claim),
    )
    result = ControlledRuntimeQueueAdmissionRecordConsumer().consume(**context)
    assert result.status == "queue_admission_record_consumption_failed"
    assert result.reason_codes == ("REGISTRY_ERROR",)

    monkeypatch.setattr(
        ControlledRuntimeQueueAdmissionRecordConsumptionRegistry,
        "claim",
        original,
    )
    registry = ControlledRuntimeQueueAdmissionRecordConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert registry.count_claims() == 0


@pytest.mark.parametrize(
    "database_path",
    ["../escape.sqlite3", "file:escape.sqlite3", "sqlite:escape", "//server/share.db"],
)
def test_unsafe_registry_paths_are_rejected(tmp_path, database_path):
    with pytest.raises(QueueAdmissionRecordConsumptionPathError):
        ControlledRuntimeQueueAdmissionRecordConsumptionRegistry(
            database_path, allowed_root=tmp_path
        )

def test_fresh_registry_read_initialization_is_durable(tmp_path):
    registry = ControlledRuntimeQueueAdmissionRecordConsumptionRegistry(
        tmp_path / "fresh.sqlite3", allowed_root=tmp_path
    )
    assert registry.count_claims() == 0
    assert registry.count_claims() == 0
    assert registry.read("missing") is None




def test_malformed_durable_payload_is_rejected(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmissionRecordConsumer().consume(**context)
    assert result.claim is not None

    connection = sqlite3.connect(context["database_path"])
    connection.execute(f"UPDATE {TABLE} SET claim_payload_json='{{}}'")
    connection.commit()
    connection.close()

    registry = ControlledRuntimeQueueAdmissionRecordConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    with pytest.raises(QueueAdmissionRecordConsumptionIntegrityError):
        registry.read(context["request"].consumption_request_id)


@pytest.mark.parametrize(
    "field,value",
    [
        ("consumption_claim_id", "stage613-record-consumption-claim-tampered"),
        ("claim_fingerprint", "0" * 64),
        ("record_fingerprint", "0" * 64),
    ],
)
def test_durable_payload_identity_tamper_is_rejected(tmp_path, field, value):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmissionRecordConsumer().consume(**context)
    assert result.claim is not None

    connection = sqlite3.connect(context["database_path"])
    payload = connection.execute(
        f"SELECT claim_payload_json FROM {TABLE}"
    ).fetchone()[0]
    replacement = payload.replace(
        f'"{field}":"{getattr(result.claim, field)}"',
        f'"{field}":"{value}"',
    )
    connection.execute(
        f"UPDATE {TABLE} SET claim_payload_json=?", (replacement,)
    )
    connection.commit()
    connection.close()

    registry = ControlledRuntimeQueueAdmissionRecordConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    with pytest.raises(QueueAdmissionRecordConsumptionIntegrityError):
        registry.read(context["request"].consumption_request_id)


def test_registry_metadata_tamper_is_rejected(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmissionRecordConsumer().consume(**context)
    assert result.claim is not None

    connection = sqlite3.connect(context["database_path"])
    connection.execute(
        "UPDATE registry_metadata SET schema_version='tampered'"
    )
    connection.commit()
    connection.close()

    registry = ControlledRuntimeQueueAdmissionRecordConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    with pytest.raises(QueueAdmissionRecordConsumptionSchemaError):
        registry.count_claims()


def test_official_verifier_can_raise_on_error(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmissionRecordConsumer().consume(**context)
    claim = result.claim
    assert claim is not None
    object.__setattr__(claim, "claim_fingerprint", "0" * 64)

    with pytest.raises(QueueAdmissionRecordConsumptionVerificationError):
        verify_controlled_runtime_queue_admission_record_consumption(
            claim,
            request=context["request"],
            stage612_record=context["stage612_record"],
            stage612_request=context["stage612_request"],
            stage612_result=context["stage612_result"],
            stage612_verification_context=context[
                "stage612_verification_context"
            ],
            persisted_payload_json=claim.to_json(),
            persistence_committed=True,
            raise_on_error=True,
        )
