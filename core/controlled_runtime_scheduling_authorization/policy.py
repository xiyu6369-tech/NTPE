"""Immutable Stage 6.6 scheduling authorization policy."""

from dataclasses import dataclass

from .models import canonical_json

SUCCESS_STATUS = "scheduling_authorized_not_consumed_not_scheduled"
SUCCESS_ACTION = "retain_for_atomic_scheduling_authorization_consumption"
BOUNDARY_KIND = "controlled_offline_acceptance_boundary"

ALLOWED_RESULT_STATUSES = (
    SUCCESS_STATUS,
    "rejected",
    "invalid_request",
    "upstream_contract_mismatch",
    "handoff_not_eligible",
    "scheduling_scope_mismatch",
    "runtime_boundary_mismatch",
    "execution_scope_mismatch",
    "verification_failed",
)
ALLOWED_RECOMMENDED_ACTIONS = (
    SUCCESS_ACTION,
    "correct_request",
    "rebuild_from_frozen_contract",
    "reject",
    "manual_integrity_review",
    "do_not_schedule",
    "do_not_execute",
)


@dataclass(frozen=True)
class ControlledRuntimeSchedulingAuthorizationPolicy:
    runtime_boundary_kind: str = BOUNDARY_KIND
    authorized_schedule_unit_count: int = 1
    complete_chain_layers: int = 19
    maximum_provider_requests: int = 1
    maximum_translation_requests: int = 1
    maximum_retries: int = 0
    maximum_fallbacks: int = 0
    schedule_once: bool = True


DEFAULT_POLICY = ControlledRuntimeSchedulingAuthorizationPolicy()


def exact_scheduling_scope(
    *,
    handoff_id: str,
    envelope_id: str,
    claim_id: str,
    consumption_id: str,
    authorization_id: str,
    execution_plan_fingerprint: str,
    execution_authorization_decision_fingerprint: str,
    stage63_claim_fingerprint: str,
    stage64_envelope_fingerprint: str,
    stage65_handoff_receipt_fingerprint: str,
    selected_adapter_index: int,
    runtime_boundary_id: str,
) -> str:
    return canonical_json({
        "authorization_id": authorization_id,
        "claim_id": claim_id,
        "consumption_id": consumption_id,
        "envelope_id": envelope_id,
        "execution_authorization_decision_fingerprint":
            execution_authorization_decision_fingerprint,
        "execution_plan_fingerprint": execution_plan_fingerprint,
        "handoff_id": handoff_id,
        "requested_schedule_unit_count": 1,
        "runtime_boundary_id": runtime_boundary_id,
        "selected_adapter_index": selected_adapter_index,
        "stage63_claim_fingerprint": stage63_claim_fingerprint,
        "stage64_envelope_fingerprint": stage64_envelope_fingerprint,
        "stage65_handoff_receipt_fingerprint":
            stage65_handoff_receipt_fingerprint,
    })
