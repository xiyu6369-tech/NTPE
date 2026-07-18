from __future__ import annotations

from .execution_policy import execution_policy
from .schema import DecisionInput, ExecutionDecision


def execution_decision(value: DecisionInput) -> ExecutionDecision:
    if not isinstance(value.provider_request_count, int) or value.provider_request_count < 0:
        raise ValueError("provider_request_count_must_be_non_negative_integer")
    policy = execution_policy(value.failure_type)
    consumed = value.execution_claim_consumed or value.provider_request_count > 0
    rollback = bool(policy.rollback_required and value.candidate_available)
    production_safe = bool(policy.production_safe and not value.production_modified)
    actions = ["execution_complete", "manual_review_required"]
    if consumed:
        actions.append("execution_consumed")
    actions.extend(("retry_forbidden", "fallback_forbidden"))
    if policy.provider_investigation_required:
        actions.append("provider_investigation_required")
    if rollback:
        actions.append("rollback_required")
    return ExecutionDecision(
        status="manual_review_required",
        actions=tuple(actions),
        retry_allowed=False,
        fallback_allowed=False,
        authorization_consumed=value.authorization_consumed,
        execution_consumed=consumed,
        rollback_required=rollback,
        manual_review_required=True,
        provider_investigation_required=policy.provider_investigation_required,
        production_safe=production_safe,
    )

