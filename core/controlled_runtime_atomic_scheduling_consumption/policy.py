"""Immutable Stage 6.7 atomic scheduling authorization consumption policy."""

from dataclasses import dataclass

from .models import canonical_json

SUCCESS_STATUS = "scheduling_authorization_consumed_not_scheduled"
SUCCESS_ACTION = "retain_for_controlled_runtime_scheduling_envelope"
BOUNDARY_KIND = "controlled_offline_acceptance_boundary"
REGISTRY_NAMESPACE = "ntpe.controlled_runtime.atomic_scheduling_consumption.v1"

ALLOWED_RESULT_STATUSES = (
    SUCCESS_STATUS,
    "already_consumed",
    "rejected",
    "invalid_request",
    "upstream_contract_mismatch",
    "scheduling_authorization_not_eligible",
    "consumption_scope_mismatch",
    "runtime_boundary_mismatch",
    "execution_scope_mismatch",
    "registry_error",
    "verification_failed",
)
ALLOWED_RECOMMENDED_ACTIONS = (
    SUCCESS_ACTION,
    "reject_replay",
    "correct_request",
    "rebuild_from_frozen_contract",
    "manual_integrity_review",
    "do_not_schedule",
    "do_not_execute",
)


@dataclass(frozen=True)
class AtomicSchedulingAuthorizationConsumptionPolicy:
    runtime_boundary_kind: str = BOUNDARY_KIND
    consumed_schedule_unit_count: int = 1
    registry_namespace: str = REGISTRY_NAMESPACE
    complete_chain_layers: int = 21
    maximum_provider_requests: int = 1
    maximum_translation_requests: int = 1
    maximum_retries: int = 0
    maximum_fallbacks: int = 0
    schedule_once: bool = True


DEFAULT_POLICY = AtomicSchedulingAuthorizationConsumptionPolicy()


def exact_consumption_scope(
    *,
    scheduling_authorization_id: str,
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
    stage66_scheduling_request_fingerprint: str,
    stage66_scheduling_decision_fingerprint: str,
    selected_adapter_index: int,
    runtime_boundary_id: str,
    runtime_boundary_kind: str,
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
        "runtime_boundary_kind": runtime_boundary_kind,
        "scheduling_authorization_id": scheduling_authorization_id,
        "selected_adapter_index": selected_adapter_index,
        "stage63_claim_fingerprint": stage63_claim_fingerprint,
        "stage64_envelope_fingerprint": stage64_envelope_fingerprint,
        "stage65_handoff_receipt_fingerprint":
            stage65_handoff_receipt_fingerprint,
        "stage66_scheduling_decision_fingerprint":
            stage66_scheduling_decision_fingerprint,
        "stage66_scheduling_request_fingerprint":
            stage66_scheduling_request_fingerprint,
    })