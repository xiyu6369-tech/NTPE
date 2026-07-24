"""Pure offline verification for Stage 6.7 scheduling-consumption claims."""

from __future__ import annotations

from .errors import AtomicSchedulingConsumptionVerificationError
from .models import (
    CLAIM_SCHEMA_NAME,
    CLAIM_SCHEMA_VERSION,
    AtomicSchedulingAuthorizationConsumptionClaim,
    AtomicSchedulingAuthorizationConsumptionRequest,
    _AtomicSchedulingConsumptionClaimVerificationResult,
    canonical_sha256,
)
from .policy import BOUNDARY_KIND, DEFAULT_POLICY, SUCCESS_STATUS


def verify_atomic_scheduling_consumption_claim(
    claim: AtomicSchedulingAuthorizationConsumptionClaim,
    *,
    request: AtomicSchedulingAuthorizationConsumptionRequest | None = None,
    stage66_scheduling_request: object | None = None,
    stage66_scheduling_decision: object | None = None,
    stage65_handoff_receipt: object | None = None,
    stage64_envelope: object | None = None,
    stage63_claim: object | None = None,
    stage62_record: object | None = None,
    authorization_decision: object | None = None,
    execution_plan: object | None = None,
    raise_on_error: bool = False,
) -> _AtomicSchedulingConsumptionClaimVerificationResult:
    if not isinstance(claim, AtomicSchedulingAuthorizationConsumptionClaim):
        raise TypeError("claim must be Stage 6.7 scheduling-consumption claim")

    reasons: list[str] = []
    chain = tuple(claim.upstream_fingerprint_chain)
    schema_ok = (
        claim.schema_name == CLAIM_SCHEMA_NAME
        and claim.schema_version == CLAIM_SCHEMA_VERSION
    )
    fingerprint_ok = (
        claim.claim_fingerprint
        == canonical_sha256(claim._fingerprint_payload(chain[:20]))
    )
    chain_ok = all((
        len(chain) == DEFAULT_POLICY.complete_chain_layers,
        len(chain) >= 21,
        chain[6] == claim.execution_plan_fingerprint,
        chain[8] == claim.execution_authorization_decision_fingerprint,
        chain[12] == claim.stage63_claim_fingerprint,
        chain[14] == claim.stage64_envelope_fingerprint,
        chain[16] == claim.stage65_handoff_receipt_fingerprint,
        chain[17] == claim.stage66_scheduling_request_fingerprint,
        chain[18] == claim.stage66_scheduling_decision_fingerprint,
        chain[19] == claim.scheduling_consumption_request_fingerprint,
        chain[20] == claim.claim_fingerprint,
    ))

    request_ok = True
    if request is not None:
        request_ok = all((
            request.request_fingerprint
            == canonical_sha256(request._fingerprint_payload()),
            claim.scheduling_consumption_request_fingerprint
            == request.request_fingerprint,
            claim.scheduling_consumption_id
            == request.scheduling_consumption_id,
            claim.scheduling_authorization_id
            == request.scheduling_authorization_id,
            claim.handoff_id == request.handoff_id,
            claim.envelope_id == request.envelope_id,
            claim.claim_id == request.claim_id,
            claim.consumption_id == request.consumption_id,
            claim.authorization_id == request.authorization_id,
            claim.execution_plan_fingerprint
            == request.execution_plan_fingerprint,
            claim.execution_authorization_decision_fingerprint
            == request.execution_authorization_decision_fingerprint,
            claim.stage63_claim_fingerprint
            == request.stage63_claim_fingerprint,
            claim.stage64_envelope_fingerprint
            == request.stage64_envelope_fingerprint,
            claim.stage65_handoff_receipt_fingerprint
            == request.stage65_handoff_receipt_fingerprint,
            claim.stage66_scheduling_request_fingerprint
            == request.stage66_scheduling_request_fingerprint,
            claim.stage66_scheduling_decision_fingerprint
            == request.stage66_scheduling_decision_fingerprint,
            claim.selected_adapter_index == request.selected_adapter_index,
            claim.runtime_boundary_id == request.runtime_boundary_id,
            claim.runtime_boundary_kind == request.runtime_boundary_kind,
        ))

    stage66_request_ok = (
        stage66_scheduling_request is None
        or all((
            claim.stage66_scheduling_request_fingerprint
            == getattr(stage66_scheduling_request, "request_fingerprint", None),
            claim.scheduling_authorization_id
            == getattr(
                stage66_scheduling_request,
                "scheduling_authorization_id",
                None,
            ),
            claim.handoff_id
            == getattr(stage66_scheduling_request, "handoff_id", None),
        ))
    )
    stage66_decision_ok = (
        stage66_scheduling_decision is None
        or all((
            claim.stage66_scheduling_decision_fingerprint
            == getattr(stage66_scheduling_decision, "decision_fingerprint", None),
            claim.scheduling_authorization_id
            == getattr(
                stage66_scheduling_decision,
                "scheduling_authorization_id",
                None,
            ),
            claim.stage66_scheduling_request_fingerprint
            == getattr(
                stage66_scheduling_decision,
                "scheduling_authorization_request_fingerprint",
                None,
            ),
            tuple(
                getattr(
                    stage66_scheduling_decision,
                    "upstream_fingerprint_chain",
                    (),
                )
            ) == chain[:19],
        ))
    )
    stage65_ok = (
        stage65_handoff_receipt is None
        or all((
            claim.handoff_id
            == getattr(stage65_handoff_receipt, "handoff_id", None),
            claim.stage65_handoff_receipt_fingerprint
            == getattr(stage65_handoff_receipt, "receipt_fingerprint", None),
            claim.runtime_boundary_id
            == getattr(stage65_handoff_receipt, "runtime_boundary_id", None),
        ))
    )
    stage64_ok = (
        stage64_envelope is None
        or all((
            claim.envelope_id == getattr(stage64_envelope, "envelope_id", None),
            claim.stage64_envelope_fingerprint
            == getattr(stage64_envelope, "envelope_fingerprint", None),
        ))
    )
    stage63_ok = (
        stage63_claim is None
        or all((
            claim.claim_id == getattr(stage63_claim, "claim_id", None),
            claim.stage63_claim_fingerprint
            == getattr(stage63_claim, "claim_fingerprint", None),
        ))
    )
    stage62_ok = (
        stage62_record is None
        or claim.consumption_id
        == getattr(stage62_record, "consumption_id", None)
    )
    stage61_ok = (
        authorization_decision is None
        or all((
            claim.authorization_id
            == getattr(authorization_decision, "authorization_id", None),
            claim.execution_authorization_decision_fingerprint
            == getattr(authorization_decision, "decision_fingerprint", None),
        ))
    )
    plan_ok = (
        execution_plan is None
        or claim.execution_plan_fingerprint
        == getattr(execution_plan, "execution_plan_fingerprint", None)
    )

    adapter_values = [claim.selected_adapter_index]
    for upstream in (
        request,
        stage66_scheduling_request,
        stage66_scheduling_decision,
        stage65_handoff_receipt,
        stage64_envelope,
        stage63_claim,
    ):
        if upstream is not None:
            adapter_values.append(getattr(upstream, "selected_adapter_index", None))
    adapter_ok = (
        type(claim.selected_adapter_index) is int
        and all(value == claim.selected_adapter_index for value in adapter_values)
    )
    unit_ok = (
        type(claim.consumed_schedule_unit_count) is int
        and claim.consumed_schedule_unit_count == 1
        and (
            request is None
            or request.requested_schedule_unit_count == 1
        )
        and (
            stage66_scheduling_decision is None
            or getattr(
                stage66_scheduling_decision,
                "authorized_schedule_unit_count",
                None,
            ) == 1
        )
    )
    boundary_ok = all((
        isinstance(claim.runtime_boundary_id, str),
        bool(claim.runtime_boundary_id),
        claim.runtime_boundary_kind == BOUNDARY_KIND,
        stage65_handoff_receipt is None
        or claim.runtime_boundary_kind
        == getattr(stage65_handoff_receipt, "runtime_boundary_kind", None),
    ))
    state_ok = all((
        claim.authorization_consumed,
        not claim.authorization_reusable,
        claim.durable_reuse_prevention_established,
        claim.persistent_registry_written,
        claim.runtime_handoff_prepared,
        claim.runtime_handoff_completed,
        claim.runtime_boundary_accepted,
        claim.scheduling_authorization_requested,
        claim.scheduling_authorized,
        claim.scheduling_authorization_consumed,
        not claim.scheduling_authorization_reusable,
        claim.schedule_once,
        claim.durable_scheduling_reuse_prevention_established,
        claim.persistent_scheduling_registry_written,
        not claim.runtime_execution_scheduled,
        not claim.queue_record_created,
        not claim.job_record_created,
        not claim.worker_started,
        not claim.execution_started,
        not claim.execution_completed,
        claim.claim_state == SUCCESS_STATUS,
    ))
    disabled_ok = not any(
        getattr(claim, name)
        for name in (
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

    checks = (
        ("INVALID_SCHEMA", schema_ok),
        ("CLAIM_FINGERPRINT_MISMATCH", fingerprint_ok),
        ("REQUEST_BINDING_MISMATCH", request_ok),
        ("STAGE66_DECISION_BINDING_MISMATCH", stage66_decision_ok),
        ("STAGE66_REQUEST_BINDING_MISMATCH", stage66_request_ok),
        ("STAGE65_BINDING_MISMATCH", stage65_ok),
        ("STAGE64_BINDING_MISMATCH", stage64_ok),
        ("STAGE63_BINDING_MISMATCH", stage63_ok),
        ("STAGE62_BINDING_MISMATCH", stage62_ok),
        ("STAGE61_BINDING_MISMATCH", stage61_ok),
        ("PLAN_BINDING_MISMATCH", plan_ok),
        ("ADAPTER_INDEX_MISMATCH", adapter_ok),
        ("UNIT_COUNT_MISMATCH", unit_ok),
        ("RUNTIME_BOUNDARY_MISMATCH", boundary_ok),
        ("UPSTREAM_CHAIN_MISMATCH", chain_ok),
        ("CLAIM_STATE_INVALID", state_ok),
        ("CAPABILITY_ENABLED", disabled_ok),
    )
    reasons.extend(code for code, valid in checks if not valid)
    result = _AtomicSchedulingConsumptionClaimVerificationResult(
        valid=not reasons,
        schema_verified=schema_ok,
        fingerprint_verified=fingerprint_ok,
        request_binding_verified=request_ok,
        stage66_decision_binding_verified=stage66_decision_ok,
        stage66_request_binding_verified=stage66_request_ok,
        stage65_binding_verified=stage65_ok,
        stage64_binding_verified=stage64_ok,
        stage63_binding_verified=stage63_ok,
        stage62_binding_verified=stage62_ok,
        stage61_binding_verified=stage61_ok,
        plan_binding_verified=plan_ok,
        adapter_index_verified=adapter_ok,
        unit_count_verified=unit_ok,
        runtime_boundary_verified=boundary_ok,
        upstream_chain_verified=chain_ok,
        state_verified=state_ok,
        capabilities_disabled=disabled_ok,
        reason_codes=tuple(reasons),
    )
    if raise_on_error and not result.valid:
        raise AtomicSchedulingConsumptionVerificationError(
            ",".join(result.reason_codes)
        )
    return result