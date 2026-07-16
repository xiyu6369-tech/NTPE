from __future__ import annotations

from .budget import calculate_request_budget
from .classification import classify_provider_failure
from .compatibility import evaluate_provider_compatibility
from .models import *
from .routing_policy import DEFAULT_ROUTING_POLICY


def evaluate_fallback_eligibility(item:ProviderRoutingInput,primary:ProviderProfile,fallback:ProviderProfile,failure:ProviderFailureEvidence,*,policy:ProviderRoutingPolicy=DEFAULT_ROUTING_POLICY)->ProviderFallbackDecision:
    reasons=[];c=classify_provider_failure(failure.failure_type)
    if not c["fallback_eligible"]:reasons.append("failure_not_fallback_eligible")
    if policy.academic_degraded_fallback!="forbidden" or "academic" in fallback.provider_id:reasons.append("academic_degraded_fallback_forbidden")
    compatibility=evaluate_provider_compatibility(item,fallback,required_quality_contract_id=primary.quality_contract_id,required_quality_contract_version=primary.quality_contract_version,required_prompt_contract_id=primary.prompt_contract_id,required_prompt_contract_version=primary.prompt_contract_version)
    if compatibility.status=="incompatible":reasons.extend(compatibility.reasons)
    budget=calculate_request_budget(item,planned_requests=1)
    if not budget["valid"] or item.current_fallback_requests+1>item.request_budget.maximum_fallback_requests:reasons.append("request_budget_exceeded")
    manual=compatibility.manual_review_required or policy.cross_provider_requires_manual_approval
    if manual and not item.manual_approval_granted:return ProviderFallbackDecision("manual_approval_required",False,fallback.provider_id,tuple(reasons)+("cross_provider_manual_approval",),True)
    return ProviderFallbackDecision("allowed" if not reasons else "blocked",not reasons,fallback.provider_id if not reasons else None,tuple(reasons),False)
