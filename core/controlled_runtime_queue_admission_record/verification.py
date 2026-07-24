"""Official Stage 6.12 offline verification."""

from __future__ import annotations

from core.controlled_runtime_queue_admission_authorization_consumption import (
    ControlledRuntimeQueueAdmissionAuthorizationConsumptionClaim,
    ControlledRuntimeQueueAdmissionAuthorizationConsumptionRequest,
    ControlledRuntimeQueueAdmissionAuthorizationConsumptionResult,
    verify_controlled_runtime_queue_admission_authorization_consumption,
)

from .errors import QueueAdmissionRecordPreparationVerificationError
from .models import (
    ControlledRuntimeQueueAdmissionRecord,
    ControlledRuntimeQueueAdmissionRecordRequest,
    ControlledRuntimeQueueAdmissionRecordVerificationResult,
    _id,
)
from .policy import (
    BOUNDARY_KIND, PREPARATION_INTENT, RECORD_SCHEMA_NAME,
    RECORD_SCHEMA_VERSION, SUCCESS_STATUS,
)
from .serialization import canonical_sha256, values


def verify_controlled_runtime_queue_admission_record(
    record: ControlledRuntimeQueueAdmissionRecord,
    *,
    request: ControlledRuntimeQueueAdmissionRecordRequest,
    stage611_claim: ControlledRuntimeQueueAdmissionAuthorizationConsumptionClaim,
    stage611_request: ControlledRuntimeQueueAdmissionAuthorizationConsumptionRequest,
    stage611_result: ControlledRuntimeQueueAdmissionAuthorizationConsumptionResult,
    stage611_verification_context: dict[str, object],
    raise_on_error: bool = False,
) -> ControlledRuntimeQueueAdmissionRecordVerificationResult:
    if not isinstance(record, ControlledRuntimeQueueAdmissionRecord):
        raise TypeError("record must be Stage 6.12 record")
    if not isinstance(request, ControlledRuntimeQueueAdmissionRecordRequest):
        raise TypeError("request must be Stage 6.12 request")
    if not isinstance(stage611_result, ControlledRuntimeQueueAdmissionAuthorizationConsumptionResult):
        raise TypeError("stage611_result must be authentic Stage 6.11 result")
    upstream = verify_controlled_runtime_queue_admission_authorization_consumption(
        stage611_claim,
        request=stage611_request,
        **stage611_verification_context,
    )
    schema_ok = (record.schema_name, record.schema_version) == (
        RECORD_SCHEMA_NAME, RECORD_SCHEMA_VERSION
    )
    request_id = _id(
        "stage612-record-request",
        values(request, exclude=("record_request_id", "request_fingerprint")),
    )
    request_fp = canonical_sha256(values(request, exclude=("request_fingerprint",)))
    record_id = _id(
        "stage612-record",
        record._payload(tuple(record.canonical_chain[:30]), queue_admission_record_id=""),
    )
    record_fp = canonical_sha256(
        record._payload(
            tuple(record.canonical_chain[:30]),
            queue_admission_record_id=record.queue_admission_record_id,
        )
    )
    identity_ok = (
        request.record_request_id == request_id
        and record.queue_admission_record_id == record_id
    )
    fingerprint_ok = (
        request.request_fingerprint == request_fp
        and record.record_fingerprint == record_fp
    )
    upstream_ok = all((
        upstream.valid,
        stage611_result.claim == stage611_claim,
        stage611_result.request == stage611_request,
        stage611_result.verification_succeeded,
        stage611_result.upstream_verified,
        stage611_result.durable_claim_created,
        stage611_result.exactly_one_authorization_consumed,
        not stage611_result.replay_detected,
        stage611_result.persistence_committed,
        stage611_result.durable_readback_verified,
    ))
    binding_ok = all((
        request.consumption_claim_id == stage611_claim.consumption_claim_id,
        request.claim_fingerprint == stage611_claim.claim_fingerprint,
        request.consumption_request_id == stage611_request.consumption_request_id,
        request.consumption_request_fingerprint == stage611_request.request_fingerprint,
        record.consumption_claim_id == request.consumption_claim_id,
        record.claim_fingerprint == request.claim_fingerprint,
        record.authorization_id == request.authorization_id,
        record.decision_fingerprint == request.decision_fingerprint,
        record.authorization_request_id == request.authorization_request_id,
        record.stage69_claim_fingerprint == request.stage69_claim_fingerprint,
        record.scheduling_envelope_fingerprint == request.scheduling_envelope_fingerprint,
        record.stage67_claim_fingerprint == request.stage67_claim_fingerprint,
        record.stage66_decision_fingerprint == request.stage66_decision_fingerprint,
        record.runtime_boundary_id == request.runtime_boundary_id,
        record.runtime_boundary_kind == BOUNDARY_KIND,
        record.selected_adapter_index == request.selected_adapter_index,
        record.capability_state_fingerprint == request.capability_state_fingerprint,
    ))
    chain_ok = all((
        tuple(request.upstream_chain) == tuple(stage611_claim.canonical_chain),
        len(record.canonical_chain) == 31,
        tuple(record.canonical_chain[:29]) == tuple(request.upstream_chain),
        record.canonical_chain[29] == request.request_fingerprint,
        record.canonical_chain[30] == record.record_fingerprint,
    ))
    state_ok = all((
        stage611_claim.queue_admission_authorization_consumed,
        not stage611_claim.queue_admission_authorization_reusable,
        not stage611_claim.queue_admission_record_prepared,
        not stage611_claim.queue_admission_record_consumed,
        not stage611_claim.queue_record_created,
        not stage611_claim.runtime_execution_scheduled,
        not stage611_claim.execution_started,
        record.scheduling_authorization_consumed,
        record.scheduling_envelope_prepared,
        record.scheduling_envelope_consumed,
        not record.scheduling_envelope_reusable,
        record.queue_admission_authorized,
        record.queue_admission_authorization_consumed,
        not record.queue_admission_authorization_reusable,
        record.queue_admission_record_prepared,
        not record.queue_admission_record_consumed,
        not record.queue_record_created,
        not record.runtime_execution_scheduled,
        not record.execution_started,
        record.persistent_registry_written,
        record.record_state == SUCCESS_STATUS,
    ))
    checks = (
        ("INVALID_SCHEMA", schema_ok),
        ("INVALID_IDENTITY", identity_ok),
        ("FINGERPRINT_MISMATCH", fingerprint_ok),
        ("UPSTREAM_VERIFICATION_FAILED", upstream_ok),
        ("BINDING_MISMATCH", binding_ok),
        ("CHAIN_MISMATCH", chain_ok),
        ("UPSTREAM_STATE_MISMATCH", state_ok),
    )
    reasons = tuple(code for code, valid in checks if not valid)
    result = ControlledRuntimeQueueAdmissionRecordVerificationResult(
        valid=not reasons,
        schema_verified=schema_ok,
        identity_verified=identity_ok,
        fingerprint_verified=fingerprint_ok,
        upstream_verified=upstream_ok,
        binding_verified=binding_ok,
        chain_verified=chain_ok,
        state_verified=state_ok,
        persistence_verified=False,
        canonical_payload_verified=False,
        reason_codes=reasons,
    )
    if raise_on_error and not result.valid:
        raise QueueAdmissionRecordPreparationVerificationError(",".join(reasons))
    return result
