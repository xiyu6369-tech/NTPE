"""Immutable Stage 6.5 handoff policy."""

from dataclasses import dataclass

SUCCESS_STATUS = "handoff_accepted_not_scheduled_not_executed"
SUCCESS_ACTION = "retain_for_controlled_scheduling_authorization"
BOUNDARY_KIND = "controlled_offline_acceptance_boundary"

ALLOWED_RESULT_STATUSES = (
    SUCCESS_STATUS, "rejected", "invalid_request", "upstream_contract_mismatch",
    "envelope_not_eligible", "handoff_scope_mismatch",
    "runtime_boundary_mismatch", "execution_scope_mismatch",
    "verification_failed",
)
ALLOWED_RECOMMENDED_ACTIONS = (
    SUCCESS_ACTION, "correct_request", "rebuild_from_frozen_contract", "reject",
    "manual_integrity_review", "do_not_schedule", "do_not_execute",
)


@dataclass(frozen=True)
class ControlledRuntimeHandoffPolicy:
    boundary_kind: str = BOUNDARY_KIND
    success_receipt_state: str = SUCCESS_STATUS
    accepted_unit_count: int = 1
    stage64_chain_layers: int = 15
    complete_chain_layers: int = 17
    max_boundary_id_length: int = 128


DEFAULT_POLICY = ControlledRuntimeHandoffPolicy()


def exact_handoff_scope(
    *, envelope_id: str, authorization_id: str, claim_id: str,
    execution_plan_fingerprint: str, selected_adapter_index: int,
    runtime_boundary_id: str,
) -> str:
    from .models import canonical_json

    return canonical_json({
        "authorization_id": authorization_id,
        "claim_id": claim_id,
        "envelope_id": envelope_id,
        "execution_plan_fingerprint": execution_plan_fingerprint,
        "requested_unit_count": 1,
        "runtime_boundary_id": runtime_boundary_id,
        "selected_adapter_index": selected_adapter_index,
    })
