"""Official offline verification for a Stage 7.1 durable queue record."""

from __future__ import annotations

from core.controlled_runtime_queue_admission_record_consumption import (
    ControlledRuntimeQueueAdmissionRecordConsumptionClaim,
    ControlledRuntimeQueueAdmissionRecordConsumptionRequest,
    ControlledRuntimeQueueAdmissionRecordConsumptionResult,
)

from .errors import ControlledRuntimeQueueAdmissionVerificationError
from .models import (
    ControlledRuntimeQueueAdmissionRequest,
    ControlledRuntimeQueueRecord,
    ControlledRuntimeQueueRecordVerificationResult,
    _id,
)
from .policy import (
    ADMISSION_INTENT,
    QUEUE_RECORD_SCHEMA_NAME,
    QUEUE_RECORD_SCHEMA_VERSION,
    REQUEST_SCHEMA_NAME,
    REQUEST_SCHEMA_VERSION,
    ControlledRuntimeQueueAdmissionPolicy,
)
from .serialization import canonical_sha256, values


def verify_controlled_runtime_queue_record(
    queue_record: ControlledRuntimeQueueRecord,
    *,
    request: ControlledRuntimeQueueAdmissionRequest,
    stage613_claim: ControlledRuntimeQueueAdmissionRecordConsumptionClaim,
    stage613_request: ControlledRuntimeQueueAdmissionRecordConsumptionRequest,
    stage613_result: ControlledRuntimeQueueAdmissionRecordConsumptionResult,
    stage613_verification_context: dict[str, object],
    persisted_payload_json: str | None = None,
    persistence_committed: bool = False,
    durable_readback_verified: bool = False,
    raise_on_error: bool = False,
) -> ControlledRuntimeQueueRecordVerificationResult:
    if not isinstance(queue_record, ControlledRuntimeQueueRecord):
        raise TypeError("queue_record must be a Stage 7.1 queue record")
    if not isinstance(request, ControlledRuntimeQueueAdmissionRequest):
        raise TypeError("request must be a Stage 7.1 admission request")
    if not isinstance(
        stage613_claim,
        ControlledRuntimeQueueAdmissionRecordConsumptionClaim,
    ):
        raise TypeError("stage613_claim must be an authentic Stage 6.13 claim")
    if not isinstance(
        stage613_request,
        ControlledRuntimeQueueAdmissionRecordConsumptionRequest,
    ):
        raise TypeError("stage613_request must be an authentic Stage 6.13 request")
    if not isinstance(
        stage613_result,
        ControlledRuntimeQueueAdmissionRecordConsumptionResult,
    ):
        raise TypeError("stage613_result must be an authentic Stage 6.13 result")

    policy_denials = ControlledRuntimeQueueAdmissionPolicy().evaluate(
        request,
        stage613_claim=stage613_claim,
        stage613_request=stage613_request,
        stage613_result=stage613_result,
        stage613_verification_context=stage613_verification_context,
    )
    schema_ok = all(
        (
            (request.schema_name, request.schema_version)
            == (REQUEST_SCHEMA_NAME, REQUEST_SCHEMA_VERSION),
            (queue_record.schema_name, queue_record.schema_version)
            == (QUEUE_RECORD_SCHEMA_NAME, QUEUE_RECORD_SCHEMA_VERSION),
        )
    )
    request_id = _id(
        "stage71-queue-admission-request",
        values(
            request,
            exclude=("admission_request_id", "request_fingerprint"),
        ),
    )
    request_fingerprint = canonical_sha256(
        values(request, exclude=("request_fingerprint",))
    )
    pre_chain = tuple(queue_record.canonical_chain[:34])
    record_id = _id(
        "stage71-runtime-queue-record",
        queue_record._payload(pre_chain, queue_record_id=""),
    )
    record_fingerprint = canonical_sha256(
        queue_record._payload(
            pre_chain,
            queue_record_id=queue_record.queue_record_id,
        )
    )
    identity_ok = all(
        (
            request.admission_request_id == request_id,
            queue_record.queue_record_id == record_id,
        )
    )
    fingerprint_ok = all(
        (
            request.request_fingerprint == request_fingerprint,
            queue_record.queue_record_fingerprint == record_fingerprint,
        )
    )
    binding_names = (
        "stage613_claim_id",
        "stage613_claim_fingerprint",
        "stage613_consumption_request_id",
        "stage613_consumption_request_fingerprint",
        "stage612_record_id",
        "stage612_record_fingerprint",
        "stage612_preparation_request_id",
        "stage612_request_fingerprint",
        "stage611_claim_id",
        "stage611_claim_fingerprint",
        "stage610_authorization_id",
        "stage610_decision_fingerprint",
        "stage610_authorization_request_id",
        "stage610_request_fingerprint",
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
    )
    binding_ok = all(
        getattr(queue_record, name) == getattr(request, name)
        for name in binding_names
    ) and all(
        (
            queue_record.admission_request_id == request.admission_request_id,
            queue_record.admission_request_fingerprint
            == request.request_fingerprint,
        )
    )
    chain_ok = all(
        (
            len(request.upstream_chain) == 33,
            tuple(request.upstream_chain)
            == tuple(stage613_claim.canonical_chain),
            len(queue_record.canonical_chain) == 35,
            tuple(queue_record.canonical_chain[:33])
            == tuple(request.upstream_chain),
            queue_record.canonical_chain[33] == request.request_fingerprint,
            queue_record.canonical_chain[34]
            == queue_record.queue_record_fingerprint,
            len(set(queue_record.canonical_chain)) == 35,
        )
    )
    expected_state = {
        "scheduling_authorization_consumed": True,
        "scheduling_envelope_prepared": True,
        "scheduling_envelope_consumed": True,
        "scheduling_envelope_reusable": False,
        "queue_admission_authorized": True,
        "queue_admission_authorization_consumed": True,
        "queue_admission_record_prepared": True,
        "queue_admission_record_consumed": True,
        "queue_admission_performed": True,
        "queue_record_created": True,
        "queue_record_consumed": False,
        "queue_record_reusable": False,
        "runtime_execution_scheduled": False,
        "execution_started": False,
        "persistent_registry_written": True,
    }
    state_ok = all(
        type(getattr(queue_record, name)) is bool
        and getattr(queue_record, name) is expected
        for name, expected in expected_state.items()
    )
    intent_ok = request.admission_intent == ADMISSION_INTENT
    persistence_ok = type(persistence_committed) is bool and persistence_committed
    readback_ok = (
        type(durable_readback_verified) is bool and durable_readback_verified
    )
    payload_ok = persisted_payload_json == queue_record.to_json()
    upstream_ok = not policy_denials

    checks = (
        ("INVALID_SCHEMA", schema_ok),
        ("INVALID_IDENTITY", identity_ok),
        ("FINGERPRINT_MISMATCH", fingerprint_ok),
        ("UPSTREAM_VERIFICATION_FAILED", upstream_ok),
        ("BINDING_MISMATCH", binding_ok),
        ("INVALID_INTENT", intent_ok),
        ("CHAIN_MISMATCH", chain_ok),
        ("INVARIANT_VIOLATION", state_ok),
        ("PERSISTENCE_NOT_PROVEN", persistence_ok),
        ("READBACK_NOT_PROVEN", readback_ok),
        ("CANONICAL_PAYLOAD_MISMATCH", payload_ok),
    )
    reasons = tuple(
        dict.fromkeys(
            tuple(policy_denials)
            + tuple(code for code, valid in checks if not valid)
        )
    )
    result = ControlledRuntimeQueueRecordVerificationResult(
        valid=not reasons,
        schema_verified=schema_ok,
        identity_verified=identity_ok,
        fingerprint_verified=fingerprint_ok,
        upstream_verified=upstream_ok,
        binding_verified=binding_ok,
        intent_verified=intent_ok,
        chain_verified=chain_ok,
        state_verified=state_ok,
        persistence_verified=persistence_ok,
        durable_readback_verified=readback_ok,
        canonical_payload_verified=payload_ok,
        reason_codes=reasons,
    )
    if raise_on_error and result.valid is not True:
        raise ControlledRuntimeQueueAdmissionVerificationError(
            ",".join(result.reason_codes)
        )
    return result
