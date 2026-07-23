"""Offline verification for committed Stage 6.3 claims."""

from __future__ import annotations

import json
from dataclasses import dataclass

from .errors import AtomicConsumptionVerificationError
from .models import (
    CLAIM_SCHEMA_NAME,
    CLAIM_SCHEMA_VERSION,
    AtomicAuthorizationConsumptionClaim,
    AtomicAuthorizationConsumptionClaimRequest,
    canonical_sha256,
)


@dataclass(frozen=True)
class _AtomicConsumptionClaimVerificationResult:
    valid: bool
    schema_verified: bool
    fingerprint_verified: bool
    request_binding_verified: bool
    stage62_binding_verified: bool
    authorization_binding_verified: bool
    plan_binding_verified: bool
    adapter_index_verified: bool
    unit_count_verified: bool
    upstream_chain_verified: bool
    state_verified: bool
    capabilities_disabled: bool
    registry_payload_verified: bool
    reason_codes: tuple[str, ...]


def verify_atomic_consumption_claim(
    claim: AtomicAuthorizationConsumptionClaim,
    *,
    request: AtomicAuthorizationConsumptionClaimRequest,
    stage62_request: object | None = None,
    stage62_record: object | None = None,
    authorization_request: object | None = None,
    authorization_decision: object | None = None,
    execution_plan: object | None = None,
    stored_payload_json: str | None = None,
    stored_claim_fingerprint: str | None = None,
    raise_on_error: bool = False,
) -> _AtomicConsumptionClaimVerificationResult:
    """Verify canonical identity, all supplied bindings, and the no-execution state."""
    reasons: list[str] = []
    schema_ok = claim.schema_name == CLAIM_SCHEMA_NAME and claim.schema_version == CLAIM_SCHEMA_VERSION
    expected_fp = canonical_sha256(claim._fingerprint_payload())
    fingerprint_ok = claim.claim_fingerprint == expected_fp
    request_ok = (
        claim.claim_request_fingerprint == request.request_fingerprint
        and request.request_fingerprint == canonical_sha256(request._fingerprint_payload())
        and claim.claim_id == request.claim_id
    )
    stage62_ok = (
        claim.stage62_request_fingerprint == request.stage62_request_fingerprint
        and claim.stage62_record_fingerprint == request.stage62_record_fingerprint
    )
    if stage62_request is not None:
        stage62_ok = stage62_ok and getattr(stage62_request, "request_fingerprint", None) == claim.stage62_request_fingerprint
    if stage62_record is not None:
        stage62_ok = (
            stage62_ok
            and getattr(stage62_record, "record_fingerprint", None) == claim.stage62_record_fingerprint
            and getattr(stage62_record, "consumption_id", None) == claim.consumption_id
        )
    auth_ok = (
        claim.authorization_id == request.authorization_id
        and claim.authorization_request_fingerprint == request.authorization_request_fingerprint
        and claim.authorization_decision_fingerprint == request.authorization_decision_fingerprint
    )
    if authorization_request is not None:
        auth_ok = auth_ok and getattr(authorization_request, "request_fingerprint", None) == claim.authorization_request_fingerprint
    if authorization_decision is not None:
        auth_ok = (
            auth_ok
            and getattr(authorization_decision, "decision_fingerprint", None) == claim.authorization_decision_fingerprint
            and getattr(authorization_decision, "authorization_id", None) == claim.authorization_id
        )
    plan_ok = claim.execution_plan_fingerprint == request.execution_plan_fingerprint
    if execution_plan is not None:
        plan_ok = plan_ok and getattr(execution_plan, "execution_plan_fingerprint", None) == claim.execution_plan_fingerprint
    adapter_ok = claim.selected_adapter_index == request.selected_adapter_index
    unit_ok = claim.consumed_unit_count == request.requested_unit_count == 1 and type(claim.consumed_unit_count) is int
    chain_ok = (
        len(claim.upstream_fingerprint_chain) == 13
        and claim.upstream_fingerprint_chain[-2] == request.request_fingerprint
        and claim.upstream_fingerprint_chain[-1] == claim.claim_fingerprint
    )
    if stage62_record is not None:
        chain_ok = chain_ok and tuple(getattr(stage62_record, "upstream_fingerprint_chain", ())) == claim.upstream_fingerprint_chain[:11]
    state_ok = all((
        claim.authorization_consumption_prepared,
        claim.authorization_consumed,
        not claim.authorization_reusable,
        claim.durable_reuse_prevention_established,
        claim.persistent_registry_written,
        not claim.execution_started,
        not claim.execution_completed,
        claim.claim_state == "durably_consumed_not_executed",
    ))
    disabled_ok = not any(getattr(claim, name) for name in (
        "runtime_execution_enabled", "provider_execution_enabled", "network_execution_enabled",
        "translation_execution_enabled", "output_write_enabled", "resume_write_enabled",
        "cache_write_enabled", "retry_enabled", "fallback_enabled", "production_hook_enabled",
    ))
    payload_ok = True
    if stored_payload_json is not None:
        try:
            payload_ok = json.loads(stored_payload_json) == json.loads(claim.to_json())
        except (TypeError, ValueError):
            payload_ok = False
    if stored_claim_fingerprint is not None:
        payload_ok = payload_ok and stored_claim_fingerprint == claim.claim_fingerprint
    checks = (
        ("INVALID_SCHEMA", schema_ok), ("CLAIM_FINGERPRINT_MISMATCH", fingerprint_ok),
        ("CLAIM_REQUEST_BINDING_MISMATCH", request_ok), ("STAGE62_BINDING_MISMATCH", stage62_ok),
        ("AUTHORIZATION_BINDING_MISMATCH", auth_ok), ("PLAN_BINDING_MISMATCH", plan_ok),
        ("ADAPTER_INDEX_MISMATCH", adapter_ok), ("UNIT_COUNT_MISMATCH", unit_ok),
        ("UPSTREAM_CHAIN_MISMATCH", chain_ok), ("CLAIM_STATE_INVALID", state_ok),
        ("CAPABILITY_ENABLED", disabled_ok), ("REGISTRY_PAYLOAD_MISMATCH", payload_ok),
    )
    reasons.extend(code for code, passed in checks if not passed)
    result = _AtomicConsumptionClaimVerificationResult(
        valid=not reasons, schema_verified=schema_ok, fingerprint_verified=fingerprint_ok,
        request_binding_verified=request_ok, stage62_binding_verified=stage62_ok,
        authorization_binding_verified=auth_ok, plan_binding_verified=plan_ok,
        adapter_index_verified=adapter_ok, unit_count_verified=unit_ok,
        upstream_chain_verified=chain_ok, state_verified=state_ok,
        capabilities_disabled=disabled_ok, registry_payload_verified=payload_ok,
        reason_codes=tuple(reasons),
    )
    if raise_on_error and not result.valid:
        raise AtomicConsumptionVerificationError(",".join(result.reason_codes))
    return result
