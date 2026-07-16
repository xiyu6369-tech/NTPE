from __future__ import annotations

from .budget import calculate_request_budget
from .classification import classify_provider_failure
from .models import *
from .routing_policy import DEFAULT_ROUTING_POLICY


def evaluate_retry_eligibility(item:ProviderRoutingInput,profile:ProviderProfile,failure:ProviderFailureEvidence,*,attempts_for_provider:int,policy:ProviderRoutingPolicy=DEFAULT_ROUTING_POLICY)->ProviderRetryDecision:
    classification=classify_provider_failure(failure.failure_type);reasons=[]
    if not classification["retryable"]:reasons.append("failure_not_retryable")
    if attempts_for_provider>=policy.maximum_attempts_per_provider or item.current_retry_requests>=policy.same_provider_retry_limit:reasons.append("same_provider_retry_limit")
    repeated=sum(x.occurrence_count for x in item.provider_failure_history if x.provider_id==profile.provider_id and x.model_id==profile.model_id and x.prompt_identity==item.prompt_identity and x.failure_type in {"read_timeout","provider_timeout"})
    if repeated>=2:reasons.append("repeated_identical_timeout")
    budget=calculate_request_budget(item,planned_requests=1)
    if not budget["valid"] or item.current_retry_requests+1>item.request_budget.maximum_retry_requests:reasons.append("request_budget_exceeded")
    return ProviderRetryDecision("allowed" if not reasons else "blocked",not reasons,tuple(reasons),1,classification["manual_approval_required"])
