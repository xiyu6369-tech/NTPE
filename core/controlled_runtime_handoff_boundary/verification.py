"""Pure offline verification for Stage 6.5 handoff receipts."""

from __future__ import annotations

from .errors import ControlledRuntimeHandoffVerificationError
from .models import (
    RECEIPT_SCHEMA_NAME,
    RECEIPT_SCHEMA_VERSION,
    ControlledRuntimeHandoffReceipt,
    ControlledRuntimeHandoffRequest,
    _RuntimeHandoffVerificationResult,
    canonical_sha256,
)
from .policy import BOUNDARY_KIND, DEFAULT_POLICY, SUCCESS_STATUS


def verify_runtime_handoff_receipt(
    receipt: ControlledRuntimeHandoffReceipt,
    *,
    request: ControlledRuntimeHandoffRequest,
    execution_plan: object,
    authorization_request: object,
    authorization_decision: object,
    stage62_request: object,
    stage62_record: object,
    stage63_claim_request: object,
    stage63_claim: object,
    stage64_envelope_request: object,
    stage64_envelope: object,
    raise_on_error: bool = False,
) -> _RuntimeHandoffVerificationResult:
    """Verify the complete receipt and its 17-layer immutable binding."""
    reasons: list[str] = []
    schema_ok = (
        receipt.schema_name == RECEIPT_SCHEMA_NAME
        and receipt.schema_version == RECEIPT_SCHEMA_VERSION
    )
    fingerprint_ok = receipt.receipt_fingerprint == canonical_sha256(
        receipt._fingerprint_payload(tuple(receipt.upstream_fingerprint_chain[:16]))
    )
    request_ok = (
        receipt.handoff_request_fingerprint == request.request_fingerprint
        and request.request_fingerprint == canonical_sha256(request._fingerprint_payload())
        and receipt.handoff_id == request.handoff_id
    )
    envelope_ok = all((
        receipt.envelope_id == request.envelope_id == getattr(stage64_envelope, "envelope_id", None),
        receipt.stage64_envelope_request_fingerprint
        == request.stage64_envelope_request_fingerprint
        == getattr(stage64_envelope_request, "request_fingerprint", None),
        receipt.stage64_envelope_fingerprint
        == request.stage64_envelope_fingerprint
        == getattr(stage64_envelope, "envelope_fingerprint", None),
    ))
    claim_ok = all((
        receipt.claim_id == request.claim_id == getattr(stage63_claim, "claim_id", None),
        receipt.stage63_claim_fingerprint
        == request.stage63_claim_fingerprint
        == getattr(stage63_claim, "claim_fingerprint", None),
        getattr(stage63_claim_request, "request_fingerprint", None)
        == getattr(stage63_claim, "claim_request_fingerprint", None),
    ))
    stage62_ok = all((
        receipt.consumption_id == request.consumption_id
        == getattr(stage62_record, "consumption_id", None),
        getattr(stage62_request, "request_fingerprint", None)
        == getattr(stage62_record, "consumption_request_fingerprint", None),
    ))
    authorization_ok = all((
        receipt.authorization_id == request.authorization_id
        == getattr(authorization_decision, "authorization_id", None),
        receipt.authorization_decision_fingerprint
        == request.authorization_decision_fingerprint
        == getattr(authorization_decision, "decision_fingerprint", None),
        getattr(authorization_request, "request_fingerprint", None)
        == getattr(authorization_decision, "authorization_request_fingerprint", None),
    ))
    plan_ok = (
        receipt.execution_plan_fingerprint == request.execution_plan_fingerprint
        == getattr(execution_plan, "execution_plan_fingerprint", None)
    )
    adapter_ok = all(
        receipt.selected_adapter_index == value
        for value in (
            request.selected_adapter_index,
            getattr(stage63_claim, "selected_adapter_index", None),
            getattr(stage64_envelope, "selected_adapter_index", None),
        )
    ) and tuple(getattr(execution_plan, "selected_adapter_unit_indices", ())) == (
        receipt.selected_adapter_index,
    )
    unit_ok = type(receipt.accepted_unit_count) is int and receipt.accepted_unit_count == 1
    boundary_ok = all((
        receipt.runtime_boundary_id == request.runtime_boundary_id,
        receipt.runtime_boundary_kind == request.runtime_boundary_kind == BOUNDARY_KIND,
    ))
    expected_chain = (
        tuple(getattr(stage64_envelope, "upstream_fingerprint_chain", ()))
        + (request.request_fingerprint, receipt.receipt_fingerprint)
    )
    chain_ok = (
        len(receipt.upstream_fingerprint_chain) == DEFAULT_POLICY.complete_chain_layers
        and receipt.upstream_fingerprint_chain == expected_chain
        and receipt.upstream_fingerprint_chain[-1] == receipt.receipt_fingerprint
    )
    state_ok = all((
        receipt.authorization_consumed,
        not receipt.authorization_reusable,
        receipt.durable_reuse_prevention_established,
        receipt.persistent_registry_written,
        receipt.runtime_handoff_prepared,
        receipt.runtime_handoff_completed,
        receipt.runtime_boundary_accepted,
        not receipt.runtime_execution_scheduled,
        not receipt.execution_started,
        not receipt.execution_completed,
        receipt.receipt_state == SUCCESS_STATUS,
    ))
    disabled_ok = not any(getattr(receipt, name) for name in (
        "runtime_execution_enabled", "provider_execution_enabled",
        "network_execution_enabled", "translation_execution_enabled",
        "output_write_enabled", "resume_write_enabled", "cache_write_enabled",
        "retry_enabled", "fallback_enabled", "production_hook_enabled",
    ))
    checks = (
        ("INVALID_SCHEMA", schema_ok),
        ("RECEIPT_FINGERPRINT_MISMATCH", fingerprint_ok),
        ("REQUEST_BINDING_MISMATCH", request_ok),
        ("ENVELOPE_BINDING_MISMATCH", envelope_ok),
        ("CLAIM_BINDING_MISMATCH", claim_ok),
        ("STAGE62_BINDING_MISMATCH", stage62_ok),
        ("AUTHORIZATION_BINDING_MISMATCH", authorization_ok),
        ("PLAN_BINDING_MISMATCH", plan_ok),
        ("ADAPTER_INDEX_MISMATCH", adapter_ok),
        ("UNIT_COUNT_MISMATCH", unit_ok),
        ("RUNTIME_BOUNDARY_MISMATCH", boundary_ok),
        ("UPSTREAM_CHAIN_MISMATCH", chain_ok),
        ("RECEIPT_STATE_INVALID", state_ok),
        ("CAPABILITY_ENABLED", disabled_ok),
    )
    reasons.extend(code for code, passed in checks if not passed)
    result = _RuntimeHandoffVerificationResult(
        valid=not reasons,
        schema_verified=schema_ok,
        fingerprint_verified=fingerprint_ok,
        request_binding_verified=request_ok,
        envelope_binding_verified=envelope_ok,
        claim_binding_verified=claim_ok,
        stage62_binding_verified=stage62_ok,
        authorization_binding_verified=authorization_ok,
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
        raise ControlledRuntimeHandoffVerificationError(",".join(result.reason_codes))
    return result
