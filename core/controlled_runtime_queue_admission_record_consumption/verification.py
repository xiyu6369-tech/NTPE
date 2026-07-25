"""Official Stage 6.13 offline verification."""

from __future__ import annotations

from core.controlled_runtime_queue_admission_authorization_consumption import (
    ControlledRuntimeQueueAdmissionAuthorizationConsumptionClaim,
    ControlledRuntimeQueueAdmissionAuthorizationConsumptionRequest,
    ControlledRuntimeQueueAdmissionAuthorizationConsumptionResult,
    verify_controlled_runtime_queue_admission_authorization_consumption,
)
from core.controlled_runtime_queue_admission_record import (
    ControlledRuntimeQueueAdmissionRecord,
    ControlledRuntimeQueueAdmissionRecordRequest,
    ControlledRuntimeQueueAdmissionRecordResult,
    verify_controlled_runtime_queue_admission_record,
)

from .errors import QueueAdmissionRecordConsumptionVerificationError
from .models import (
    ControlledRuntimeQueueAdmissionRecordConsumptionClaim,
    ControlledRuntimeQueueAdmissionRecordConsumptionRequest,
    ControlledRuntimeQueueAdmissionRecordConsumptionVerificationResult,
    _id,
)
from .policy import (
    BOUNDARY_KIND,
    CLAIM_SCHEMA_NAME,
    CLAIM_SCHEMA_VERSION,
    CONSUMPTION_INTENT,
    SUCCESS_STATUS,
)
from .serialization import canonical_sha256, canonical_json, values


def verify_controlled_runtime_queue_admission_record_consumption(
    claim: ControlledRuntimeQueueAdmissionRecordConsumptionClaim,
    *,
    request: ControlledRuntimeQueueAdmissionRecordConsumptionRequest,
    stage612_record: ControlledRuntimeQueueAdmissionRecord,
    stage612_request: ControlledRuntimeQueueAdmissionRecordRequest,
    stage612_result: ControlledRuntimeQueueAdmissionRecordResult,
    stage612_verification_context: dict[str, object],
    persisted_payload_json: str | None = None,
    persistence_committed: bool = False,
    raise_on_error: bool = False,
) -> ControlledRuntimeQueueAdmissionRecordConsumptionVerificationResult:
    if not isinstance(claim, ControlledRuntimeQueueAdmissionRecordConsumptionClaim):
        raise TypeError("claim must be Stage 6.13 claim")
    if not isinstance(request, ControlledRuntimeQueueAdmissionRecordConsumptionRequest):
        raise TypeError("request must be Stage 6.13 request")
    if not isinstance(stage612_record, ControlledRuntimeQueueAdmissionRecord):
        raise TypeError("stage612_record must be authentic Stage 6.12 record")
    if not isinstance(stage612_result, ControlledRuntimeQueueAdmissionRecordResult):
        raise TypeError("stage612_result must be authentic Stage 6.12 result")

    upstream_612 = verify_controlled_runtime_queue_admission_record(
        stage612_record,
        request=stage612_request,
        **stage612_verification_context,
    )

    schema_ok = (claim.schema_name, claim.schema_version) == (
        CLAIM_SCHEMA_NAME,
        CLAIM_SCHEMA_VERSION,
    )

    request_id = _id(
        "stage613-record-consumption-request",
        values(request, exclude=("consumption_request_id", "request_fingerprint")),
    )
    request_fp = canonical_sha256(
        values(request, exclude=("request_fingerprint",))
    )
    claim_id = _id(
        "stage613-record-consumption-claim",
        claim._payload(tuple(claim.canonical_chain[:32]), consumption_claim_id=""),
    )
    claim_fp = canonical_sha256(
        claim._payload(
            tuple(claim.canonical_chain[:32]),
            consumption_claim_id=claim.consumption_claim_id,
        )
    )

    identity_ok = (
        request.consumption_request_id == request_id
        and claim.consumption_claim_id == claim_id
    )
    fingerprint_ok = (
        request.request_fingerprint == request_fp
        and claim.claim_fingerprint == claim_fp
    )

    upstream_ok = all((
        upstream_612.valid,
        stage612_result.record == stage612_record,
        stage612_result.request == stage612_request,
        stage612_result.verification_succeeded,
        stage612_result.upstream_verified,
        stage612_result.exactly_one_record_prepared,
        not stage612_result.replay_detected,
    ))

    binding_ok = all((
        request.record_id == stage612_record.queue_admission_record_id,
        request.record_fingerprint == stage612_record.record_fingerprint,
        request.record_request_id == stage612_request.record_request_id,
        request.record_request_fingerprint == stage612_request.request_fingerprint,
        request.consumption_claim_id == stage612_record.consumption_claim_id,
        request.claim_fingerprint == stage612_record.claim_fingerprint,
        request.upstream_consumption_request_id == stage612_record.consumption_request_id,
        request.consumption_request_fingerprint == stage612_record.consumption_request_fingerprint,
        request.authorization_id == stage612_record.authorization_id,
        request.decision_fingerprint == stage612_record.decision_fingerprint,
        request.authorization_request_id == stage612_record.authorization_request_id,
        request.authorization_request_fingerprint == stage612_record.authorization_request_fingerprint,
        request.stage69_claim_fingerprint == stage612_record.stage69_claim_fingerprint,
        request.scheduling_envelope_fingerprint == stage612_record.scheduling_envelope_fingerprint,
        request.stage67_claim_fingerprint == stage612_record.stage67_claim_fingerprint,
        request.stage66_decision_fingerprint == stage612_record.stage66_decision_fingerprint,
        request.runtime_boundary_id == stage612_record.runtime_boundary_id,
        request.runtime_boundary_kind == BOUNDARY_KIND,
        request.selected_adapter_index == stage612_record.selected_adapter_index,
        request.capability_state_fingerprint == stage612_record.capability_state_fingerprint,
        request.admission_class == stage612_record.admission_class,
        request.priority_class == stage612_record.priority_class,
        claim.record_id == request.record_id,
        claim.record_fingerprint == request.record_fingerprint,
        claim.authorization_id == request.authorization_id,
        claim.decision_fingerprint == request.decision_fingerprint,
        claim.runtime_boundary_id == request.runtime_boundary_id,
        claim.runtime_boundary_kind == BOUNDARY_KIND,
    ))

    chain_ok = all((
        tuple(request.upstream_chain) == tuple(stage612_record.canonical_chain),
        len(claim.canonical_chain) == 33,
        tuple(claim.canonical_chain[:31]) == tuple(request.upstream_chain),
        claim.canonical_chain[31] == request.request_fingerprint,
        claim.canonical_chain[32] == claim.claim_fingerprint,
    ))

    state_ok = all((
        stage612_record.queue_admission_record_prepared,
        not stage612_record.queue_admission_record_consumed,
        not stage612_record.queue_record_created,
        not stage612_record.runtime_execution_scheduled,
        not stage612_record.execution_started,
        claim.scheduling_authorization_consumed,
        claim.scheduling_envelope_prepared,
        claim.scheduling_envelope_consumed,
        not claim.scheduling_envelope_reusable,
        claim.queue_admission_authorized,
        claim.queue_admission_authorization_consumed,
        not claim.queue_admission_authorization_reusable,
        claim.queue_admission_record_prepared,
        claim.queue_admission_record_consumed,
        not claim.queue_admission_record_reusable,
        not claim.queue_record_created,
        not claim.runtime_execution_scheduled,
        not claim.execution_started,
        claim.persistent_registry_written,
        claim.claim_state == SUCCESS_STATUS,
    ))

    persist_ok = persistence_committed is True
    payload_ok = persisted_payload_json == claim.to_json()

    checks = (
        ("INVALID_SCHEMA", schema_ok),
        ("INVALID_IDENTITY", identity_ok),
        ("FINGERPRINT_MISMATCH", fingerprint_ok),
        ("UPSTREAM_VERIFICATION_FAILED", upstream_ok),
        ("BINDING_MISMATCH", binding_ok),
        ("CHAIN_MISMATCH", chain_ok),
        ("UPSTREAM_STATE_MISMATCH", state_ok),
        ("PERSISTENCE_NOT_PROVEN", persist_ok),
        ("CANONICAL_PAYLOAD_MISMATCH", payload_ok),
    )
    reasons = tuple(code for code, valid in checks if not valid)
    result = ControlledRuntimeQueueAdmissionRecordConsumptionVerificationResult(
        valid=not reasons,
        schema_verified=schema_ok,
        identity_verified=identity_ok,
        fingerprint_verified=fingerprint_ok,
        upstream_verified=upstream_ok,
        binding_verified=binding_ok,
        chain_verified=chain_ok,
        state_verified=state_ok,
        persistence_verified=persist_ok,
        canonical_payload_verified=payload_ok,
        reason_codes=reasons,
    )
    if raise_on_error and not result.valid:
        raise QueueAdmissionRecordConsumptionVerificationError(
            ",".join(reasons)
        )
    return result