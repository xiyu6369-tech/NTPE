"""Offline Stage 6.9 durable-claim verification."""

from __future__ import annotations

from core.controlled_runtime_scheduling_envelope import (
    ControlledRuntimeSchedulingEnvelope,
    ControlledRuntimeSchedulingEnvelopeRequest,
    verify_controlled_runtime_scheduling_envelope,
)

from .errors import SchedulingEnvelopeConsumptionVerificationError
from .models import (
    ControlledRuntimeSchedulingEnvelopeConsumptionClaim,
    ControlledRuntimeSchedulingEnvelopeConsumptionRequest,
    ControlledRuntimeSchedulingEnvelopeConsumptionVerificationResult,
    _derived_id,
)
from .policy import (
    BOUNDARY_KIND,
    CLAIM_SCHEMA_NAME,
    CLAIM_SCHEMA_VERSION,
    SUCCESS_STATUS,
)
from .serialization import canonical_sha256, model_values


def verify_controlled_runtime_scheduling_envelope_consumption(
    claim: ControlledRuntimeSchedulingEnvelopeConsumptionClaim,
    *,
    request: ControlledRuntimeSchedulingEnvelopeConsumptionRequest,
    scheduling_envelope: ControlledRuntimeSchedulingEnvelope,
    scheduling_envelope_request: ControlledRuntimeSchedulingEnvelopeRequest,
    stage67_scheduling_consumption_request: object,
    stage67_scheduling_consumption_claim: object,
    stage66_scheduling_decision: object,
    stage65_handoff_receipt: object,
    stage64_envelope: object,
    stage63_claim: object,
    stage62_record: object,
    authorization_decision: object,
    execution_plan: object,
    persisted_payload_json: str | None = None,
    persistence_committed: bool = False,
    raise_on_error: bool = False,
) -> ControlledRuntimeSchedulingEnvelopeConsumptionVerificationResult:
    if not isinstance(
        claim, ControlledRuntimeSchedulingEnvelopeConsumptionClaim
    ):
        raise TypeError("claim must be a Stage 6.9 consumption claim")
    if not isinstance(
        request, ControlledRuntimeSchedulingEnvelopeConsumptionRequest
    ):
        raise TypeError("request must be a Stage 6.9 consumption request")
    if not isinstance(scheduling_envelope, ControlledRuntimeSchedulingEnvelope):
        raise TypeError("scheduling_envelope must be an authentic Stage 6.8 envelope")
    if not isinstance(
        scheduling_envelope_request, ControlledRuntimeSchedulingEnvelopeRequest
    ):
        raise TypeError("scheduling_envelope_request must be Stage 6.8 request")

    upstream = verify_controlled_runtime_scheduling_envelope(
        scheduling_envelope,
        request=scheduling_envelope_request,
        stage67_scheduling_consumption_request=
            stage67_scheduling_consumption_request,
        stage67_scheduling_consumption_claim=stage67_scheduling_consumption_claim,
        stage66_scheduling_decision=stage66_scheduling_decision,
        stage65_handoff_receipt=stage65_handoff_receipt,
        stage64_envelope=stage64_envelope,
        stage63_claim=stage63_claim,
        stage62_record=stage62_record,
        authorization_decision=authorization_decision,
        execution_plan=execution_plan,
    )
    request_identity = request.consumption_request_id == _derived_id(
        "stage69-request",
        model_values(
            request,
            exclude=("consumption_request_id", "request_fingerprint"),
        ),
    )
    request_fingerprint = request.request_fingerprint == canonical_sha256(
        model_values(request, exclude=("request_fingerprint",))
    )
    claim_identity = claim.consumption_claim_id == _derived_id(
        "stage69-claim",
        claim._fingerprint_payload(
            tuple(claim.canonical_chain[:24]),
            claim_id="",
        ),
    )
    claim_fingerprint = claim.claim_fingerprint == canonical_sha256(
        claim._fingerprint_payload(
            tuple(claim.canonical_chain[:24]),
            claim_id=claim.consumption_claim_id,
        )
    )
    schema_ok = (
        claim.schema_name == CLAIM_SCHEMA_NAME
        and claim.schema_version == CLAIM_SCHEMA_VERSION
    )
    envelope_ok = all(
        (
            request.scheduling_envelope_id
            == scheduling_envelope.scheduling_envelope_id,
            request.scheduling_envelope_fingerprint
            == scheduling_envelope.scheduling_envelope_fingerprint,
            request.scheduling_envelope_request_id
            == scheduling_envelope_request.scheduling_envelope_id,
            request.scheduling_envelope_request_fingerprint
            == scheduling_envelope_request.request_fingerprint,
            claim.scheduling_envelope_id == request.scheduling_envelope_id,
            claim.scheduling_envelope_fingerprint
            == request.scheduling_envelope_fingerprint,
        )
    )
    upstream_binding = all(
        (
            upstream.valid,
            request.stage67_consumption_claim_id
            == getattr(
                stage67_scheduling_consumption_claim,
                "scheduling_consumption_id",
                None,
            ),
            request.stage67_claim_fingerprint
            == getattr(
                stage67_scheduling_consumption_claim,
                "claim_fingerprint",
                None,
            ),
            request.stage66_scheduling_authorization_id
            == getattr(
                stage66_scheduling_decision,
                "scheduling_authorization_id",
                None,
            ),
            request.stage66_decision_fingerprint
            == getattr(stage66_scheduling_decision, "decision_fingerprint", None),
            request.selected_adapter_index
            == scheduling_envelope.selected_adapter_index,
            claim.stage67_claim_fingerprint == request.stage67_claim_fingerprint,
            claim.stage66_decision_fingerprint
            == request.stage66_decision_fingerprint,
        )
    )
    chain_ok = all(
        (
            len(request.upstream_fingerprint_chain) == 23,
            tuple(request.upstream_fingerprint_chain)
            == tuple(scheduling_envelope.upstream_fingerprint_chain),
            len(claim.canonical_chain) == 25,
            tuple(claim.canonical_chain[:23])
            == tuple(request.upstream_fingerprint_chain),
            claim.canonical_chain[23] == request.request_fingerprint,
            claim.canonical_chain[24] == claim.claim_fingerprint,
        )
    )
    boundary_ok = all(
        (
            request.runtime_boundary_id == scheduling_envelope.runtime_boundary_id,
            claim.runtime_boundary_id == request.runtime_boundary_id,
            request.runtime_boundary_kind == BOUNDARY_KIND,
            claim.runtime_boundary_kind == BOUNDARY_KIND,
        )
    )
    unit_ok = (
        type(request.unit_scope) is int
        and request.unit_scope == 1
        and type(claim.unit_scope) is int
        and claim.unit_scope == 1
    )
    state_ok = all(
        (
            scheduling_envelope.scheduling_authorization_consumed,
            scheduling_envelope.scheduling_envelope_prepared,
            not scheduling_envelope.scheduling_envelope_consumed,
            not scheduling_envelope.scheduling_envelope_reusable,
            claim.scheduling_authorization_consumed,
            claim.scheduling_envelope_prepared,
            claim.scheduling_envelope_consumed,
            not claim.scheduling_envelope_reusable,
            not claim.queue_admission_authorized,
            not claim.runtime_execution_scheduled,
            not claim.queue_record_created,
            not claim.execution_started,
            claim.persistent_registry_written,
            claim.claim_state == SUCCESS_STATUS,
        )
    )
    persistence_ok = persistence_committed is True
    payload_ok = (
        persisted_payload_json is not None
        and persisted_payload_json == claim.to_json()
    )
    checks = (
        ("INVALID_SCHEMA", schema_ok),
        ("IDENTITY_MISMATCH", request_identity and claim_identity),
        (
            "FINGERPRINT_MISMATCH",
            request_fingerprint and claim_fingerprint,
        ),
        ("ENVELOPE_BINDING_MISMATCH", envelope_ok),
        ("UPSTREAM_BINDING_MISMATCH", upstream_binding),
        ("CHAIN_MISMATCH", chain_ok),
        ("RUNTIME_BOUNDARY_MISMATCH", boundary_ok),
        ("UNIT_SCOPE_MISMATCH", unit_ok),
        ("STATE_INVARIANT_MISMATCH", state_ok),
        ("PERSISTENCE_NOT_PROVEN", persistence_ok),
        ("CANONICAL_PAYLOAD_MISMATCH", payload_ok),
    )
    reasons = tuple(code for code, valid in checks if not valid)
    result = ControlledRuntimeSchedulingEnvelopeConsumptionVerificationResult(
        valid=not reasons,
        schema_verified=schema_ok,
        identity_verified=request_identity and claim_identity,
        fingerprint_verified=request_fingerprint and claim_fingerprint,
        envelope_binding_verified=envelope_ok,
        upstream_binding_verified=upstream_binding,
        chain_verified=chain_ok,
        runtime_boundary_verified=boundary_ok,
        unit_scope_verified=unit_ok,
        state_verified=state_ok,
        persistence_verified=persistence_ok,
        canonical_payload_verified=payload_ok,
        reason_codes=reasons,
    )
    if raise_on_error and not result.valid:
        raise SchedulingEnvelopeConsumptionVerificationError(",".join(reasons))
    return result

