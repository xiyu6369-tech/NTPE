"""Official Stage 6.10 offline verification."""

from __future__ import annotations

from core.controlled_runtime_scheduling_envelope_consumption import (
    ControlledRuntimeSchedulingEnvelopeConsumptionClaim,
    ControlledRuntimeSchedulingEnvelopeConsumptionRequest,
    ControlledRuntimeSchedulingEnvelopeConsumptionResult,
    verify_controlled_runtime_scheduling_envelope_consumption,
)

from .errors import QueueAdmissionAuthorizationVerificationError
from .models import (
    ControlledRuntimeQueueAdmissionAuthorizationDecision,
    ControlledRuntimeQueueAdmissionAuthorizationRequest,
    ControlledRuntimeQueueAdmissionAuthorizationVerificationResult,
    _id,
)
from .policy import AUTHORIZED_STATUS, DECISION_SCHEMA_NAME, DECISION_SCHEMA_VERSION
from .serialization import canonical_sha256, model_values


def verify_controlled_runtime_queue_admission_authorization(
    decision: ControlledRuntimeQueueAdmissionAuthorizationDecision,
    *,
    request: ControlledRuntimeQueueAdmissionAuthorizationRequest,
    stage69_claim: ControlledRuntimeSchedulingEnvelopeConsumptionClaim,
    stage69_request: ControlledRuntimeSchedulingEnvelopeConsumptionRequest,
    stage69_result: ControlledRuntimeSchedulingEnvelopeConsumptionResult,
    stage69_verification_context: dict[str, object],
    raise_on_error: bool = False,
) -> ControlledRuntimeQueueAdmissionAuthorizationVerificationResult:
    if not isinstance(decision, ControlledRuntimeQueueAdmissionAuthorizationDecision):
        raise TypeError("decision must be Stage 6.10 decision")
    if not isinstance(request, ControlledRuntimeQueueAdmissionAuthorizationRequest):
        raise TypeError("request must be Stage 6.10 request")
    if not isinstance(stage69_result, ControlledRuntimeSchedulingEnvelopeConsumptionResult):
        raise TypeError("stage69_result must be authentic Stage 6.9 result")
    upstream = verify_controlled_runtime_scheduling_envelope_consumption(
        stage69_claim, request=stage69_request, **stage69_verification_context
    )
    schema_ok = (decision.schema_name, decision.schema_version) == (
        DECISION_SCHEMA_NAME, DECISION_SCHEMA_VERSION
    )
    request_id = _id(
        "stage610-request",
        model_values(request, exclude=("authorization_request_id", "request_fingerprint")),
    )
    request_fp = canonical_sha256(model_values(request, exclude=("request_fingerprint",)))
    decision_id = _id(
        "stage610-authorization",
        decision._payload(tuple(decision.canonical_chain[:26]), authorization_id=""),
    )
    decision_fp = canonical_sha256(
        decision._payload(
            tuple(decision.canonical_chain[:26]),
            authorization_id=decision.authorization_id,
        )
    )
    identity_ok = (
        request.authorization_request_id == request_id
        and decision.authorization_id == decision_id
    )
    fingerprint_ok = (
        request.request_fingerprint == request_fp
        and decision.decision_fingerprint == decision_fp
    )
    upstream_ok = all((
        upstream.valid,
        stage69_result.claim == stage69_claim,
        stage69_result.request == stage69_request,
        stage69_result.verification_succeeded,
        stage69_result.upstream_verification_succeeded,
        stage69_result.durable_claim_created,
        stage69_result.exactly_one_envelope_consumed,
        not stage69_result.replay_detected,
        stage69_result.persistence_committed,
        stage69_result.durable_readback_verified,
    ))
    binding_ok = all((
        request.stage69_consumption_claim_id == stage69_claim.consumption_claim_id,
        request.stage69_claim_fingerprint == stage69_claim.claim_fingerprint,
        request.stage69_consumption_request_id == stage69_request.consumption_request_id,
        request.stage69_request_fingerprint == stage69_request.request_fingerprint,
        decision.stage69_consumption_claim_id == request.stage69_consumption_claim_id,
        decision.scheduling_envelope_fingerprint == request.scheduling_envelope_fingerprint,
        decision.stage67_claim_fingerprint == request.stage67_claim_fingerprint,
        decision.stage66_decision_fingerprint == request.stage66_decision_fingerprint,
        decision.runtime_boundary_id == request.runtime_boundary_id,
        decision.selected_adapter_index == request.selected_adapter_index,
        decision.capability_state_fingerprint == request.capability_state_fingerprint,
    ))
    chain_ok = all((
        tuple(request.upstream_chain) == tuple(stage69_claim.canonical_chain),
        len(decision.canonical_chain) == 27,
        tuple(decision.canonical_chain[:25]) == tuple(request.upstream_chain),
        decision.canonical_chain[25] == request.request_fingerprint,
        decision.canonical_chain[26] == decision.decision_fingerprint,
    ))
    state_ok = all((
        stage69_claim.scheduling_authorization_consumed,
        stage69_claim.scheduling_envelope_prepared,
        stage69_claim.scheduling_envelope_consumed,
        not stage69_claim.scheduling_envelope_reusable,
        not stage69_claim.queue_admission_authorized,
        not stage69_claim.runtime_execution_scheduled,
        not stage69_claim.queue_record_created,
        not stage69_claim.execution_started,
        decision.authorization_status == AUTHORIZED_STATUS,
        decision.queue_admission_authorized,
        not decision.queue_admission_authorization_consumed,
        not decision.queue_admission_record_prepared,
        not decision.queue_admission_record_consumed,
        not decision.queue_record_created,
        not decision.runtime_execution_scheduled,
        not decision.execution_started,
    ))
    checks = (
        ("INVALID_SCHEMA", schema_ok), ("INVALID_IDENTITY", identity_ok),
        ("FINGERPRINT_MISMATCH", fingerprint_ok),
        ("UPSTREAM_VERIFICATION_FAILED", upstream_ok),
        ("INVARIANT_VIOLATION", binding_ok),
        ("CHAIN_MISMATCH", chain_ok), ("UPSTREAM_STATE_MISMATCH", state_ok),
    )
    reasons = tuple(code for code, valid in checks if not valid)
    result = ControlledRuntimeQueueAdmissionAuthorizationVerificationResult(
        valid=not reasons, schema_verified=schema_ok,
        identity_verified=identity_ok, fingerprint_verified=fingerprint_ok,
        upstream_verified=upstream_ok, binding_verified=binding_ok,
        chain_verified=chain_ok, state_verified=state_ok, reason_codes=reasons,
    )
    if raise_on_error and not result.valid:
        raise QueueAdmissionAuthorizationVerificationError(",".join(reasons))
    return result
