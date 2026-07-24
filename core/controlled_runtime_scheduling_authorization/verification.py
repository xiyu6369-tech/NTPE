"""Pure offline verification for Stage 6.6 decisions."""

from __future__ import annotations

from .errors import (
    ControlledRuntimeSchedulingAuthorizationVerificationError,
)
from .models import (
    DECISION_SCHEMA_NAME,
    DECISION_SCHEMA_VERSION,
    ControlledRuntimeSchedulingAuthorizationDecision,
    ControlledRuntimeSchedulingAuthorizationRequest,
    _SchedulingAuthorizationDecisionVerificationResult,
    canonical_sha256,
)
from .policy import BOUNDARY_KIND, DEFAULT_POLICY, SUCCESS_STATUS


def verify_scheduling_authorization_decision(
    decision: ControlledRuntimeSchedulingAuthorizationDecision,
    *,
    request: ControlledRuntimeSchedulingAuthorizationRequest,
    execution_plan: object,
    authorization_request: object,
    authorization_decision: object,
    stage62_request: object,
    stage62_record: object,
    stage63_claim_request: object,
    stage63_claim: object,
    stage64_envelope_request: object,
    stage64_envelope: object,
    stage65_handoff_request: object,
    stage65_handoff_receipt: object,
    raise_on_error: bool = False,
) -> _SchedulingAuthorizationDecisionVerificationResult:
    reasons: list[str] = []
    schema_ok = (
        decision.schema_name == DECISION_SCHEMA_NAME
        and decision.schema_version == DECISION_SCHEMA_VERSION
    )
    fingerprint_ok = decision.decision_fingerprint == canonical_sha256(
        decision._fingerprint_payload(
            tuple(decision.upstream_fingerprint_chain[:18])
        )
    )
    request_ok = all((
        decision.scheduling_authorization_request_fingerprint
        == request.request_fingerprint,
        request.request_fingerprint
        == canonical_sha256(request._fingerprint_payload()),
        decision.scheduling_authorization_id
        == request.scheduling_authorization_id,
    ))
    handoff_ok = all((
        decision.handoff_id == request.handoff_id
        == getattr(stage65_handoff_receipt, "handoff_id", None),
        decision.stage65_handoff_request_fingerprint
        == request.stage65_handoff_request_fingerprint
        == getattr(stage65_handoff_request, "request_fingerprint", None),
        decision.stage65_handoff_receipt_fingerprint
        == request.stage65_handoff_receipt_fingerprint
        == getattr(stage65_handoff_receipt, "receipt_fingerprint", None),
    ))
    envelope_ok = all((
        decision.envelope_id == request.envelope_id
        == getattr(stage64_envelope, "envelope_id", None),
        decision.stage64_envelope_fingerprint
        == request.stage64_envelope_fingerprint
        == getattr(stage64_envelope, "envelope_fingerprint", None),
        getattr(stage64_envelope_request, "request_fingerprint", None)
        == getattr(stage64_envelope, "envelope_request_fingerprint", None),
    ))
    claim_ok = all((
        decision.claim_id == request.claim_id
        == getattr(stage63_claim, "claim_id", None),
        decision.stage63_claim_fingerprint
        == request.stage63_claim_fingerprint
        == getattr(stage63_claim, "claim_fingerprint", None),
        getattr(stage63_claim_request, "request_fingerprint", None)
        == getattr(stage63_claim, "claim_request_fingerprint", None),
    ))
    stage62_ok = all((
        decision.consumption_id == request.consumption_id
        == getattr(stage62_record, "consumption_id", None),
        getattr(stage62_request, "request_fingerprint", None)
        == getattr(stage62_record, "consumption_request_fingerprint", None),
    ))
    authorization_ok = all((
        decision.authorization_id == request.authorization_id
        == getattr(authorization_decision, "authorization_id", None),
        decision.execution_authorization_decision_fingerprint
        == request.execution_authorization_decision_fingerprint
        == getattr(authorization_decision, "decision_fingerprint", None),
        getattr(authorization_request, "request_fingerprint", None)
        == getattr(authorization_decision,
                   "authorization_request_fingerprint", None),
    ))
    plan_ok = (
        decision.execution_plan_fingerprint
        == request.execution_plan_fingerprint
        == getattr(execution_plan, "execution_plan_fingerprint", None)
    )
    adapter_ok = all(
        decision.selected_adapter_index == value for value in (
            request.selected_adapter_index,
            getattr(stage65_handoff_receipt, "selected_adapter_index", None),
            getattr(stage64_envelope, "selected_adapter_index", None),
            getattr(stage63_claim, "selected_adapter_index", None),
        )
    )
    unit_ok = (
        type(decision.authorized_schedule_unit_count) is int
        and decision.authorized_schedule_unit_count == 1
        and request.requested_schedule_unit_count == 1
    )
    boundary_ok = all((
        decision.runtime_boundary_id == request.runtime_boundary_id
        == getattr(stage65_handoff_receipt, "runtime_boundary_id", None),
        decision.runtime_boundary_kind == request.runtime_boundary_kind
        == getattr(stage65_handoff_receipt, "runtime_boundary_kind", None)
        == BOUNDARY_KIND,
    ))
    expected_chain = (
        tuple(getattr(stage65_handoff_receipt,
                      "upstream_fingerprint_chain", ()))
        + (request.request_fingerprint, decision.decision_fingerprint)
    )
    chain_ok = (
        len(decision.upstream_fingerprint_chain)
        == DEFAULT_POLICY.complete_chain_layers
        and decision.upstream_fingerprint_chain == expected_chain
        and decision.upstream_fingerprint_chain[-1]
        == decision.decision_fingerprint
    )
    state_ok = all((
        decision.authorization_consumed,
        not decision.authorization_reusable,
        decision.durable_reuse_prevention_established,
        decision.persistent_registry_written,
        decision.runtime_handoff_prepared,
        decision.runtime_handoff_completed,
        decision.runtime_boundary_accepted,
        decision.scheduling_authorization_requested,
        decision.scheduling_authorized,
        not decision.scheduling_authorization_consumed,
        not decision.scheduling_authorization_reusable,
        decision.schedule_once,
        not decision.runtime_execution_scheduled,
        not decision.queue_record_created,
        not decision.job_record_created,
        not decision.worker_started,
        not decision.execution_started,
        not decision.execution_completed,
        decision.decision_state == SUCCESS_STATUS,
    ))
    disabled_ok = not any(getattr(decision, name) for name in (
        "runtime_execution_enabled", "provider_execution_enabled",
        "network_execution_enabled", "translation_execution_enabled",
        "output_write_enabled", "resume_write_enabled", "cache_write_enabled",
        "retry_enabled", "fallback_enabled", "production_hook_enabled",
    ))
    checks = (
        ("INVALID_SCHEMA", schema_ok),
        ("DECISION_FINGERPRINT_MISMATCH", fingerprint_ok),
        ("REQUEST_BINDING_MISMATCH", request_ok),
        ("HANDOFF_BINDING_MISMATCH", handoff_ok),
        ("ENVELOPE_BINDING_MISMATCH", envelope_ok),
        ("CLAIM_BINDING_MISMATCH", claim_ok),
        ("STAGE62_BINDING_MISMATCH", stage62_ok),
        ("AUTHORIZATION_BINDING_MISMATCH", authorization_ok),
        ("PLAN_BINDING_MISMATCH", plan_ok),
        ("ADAPTER_INDEX_MISMATCH", adapter_ok),
        ("UNIT_COUNT_MISMATCH", unit_ok),
        ("RUNTIME_BOUNDARY_MISMATCH", boundary_ok),
        ("UPSTREAM_CHAIN_MISMATCH", chain_ok),
        ("DECISION_STATE_INVALID", state_ok),
        ("CAPABILITY_ENABLED", disabled_ok),
    )
    reasons.extend(code for code, passed in checks if not passed)
    result = _SchedulingAuthorizationDecisionVerificationResult(
        valid=not reasons, schema_verified=schema_ok,
        fingerprint_verified=fingerprint_ok,
        request_binding_verified=request_ok,
        handoff_binding_verified=handoff_ok,
        envelope_binding_verified=envelope_ok, claim_binding_verified=claim_ok,
        stage62_binding_verified=stage62_ok,
        authorization_binding_verified=authorization_ok,
        plan_binding_verified=plan_ok, adapter_index_verified=adapter_ok,
        unit_count_verified=unit_ok, runtime_boundary_verified=boundary_ok,
        upstream_chain_verified=chain_ok, state_verified=state_ok,
        capabilities_disabled=disabled_ok, reason_codes=tuple(reasons),
    )
    if raise_on_error and not result.valid:
        raise ControlledRuntimeSchedulingAuthorizationVerificationError(
            ",".join(result.reason_codes)
        )
    return result
