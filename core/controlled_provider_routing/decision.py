from __future__ import annotations

import hashlib,json
from dataclasses import asdict
from .budget import calculate_request_budget
from .cache_identity import build_provider_route_identity
from .compatibility import evaluate_provider_compatibility
from .models import *
from .provider_profiles import QUALITY_CONTRACT
from .routing_policy import DEFAULT_ROUTING_POLICY
from .validation import validate_routing_input


def create_routing_input(**values)->ProviderRoutingInput:return ProviderRoutingInput(**values)


def select_provider_route(item:ProviderRoutingInput,provider_profiles:tuple[ProviderProfile,...],*,routing_policy:ProviderRoutingPolicy=DEFAULT_ROUTING_POLICY)->ProviderRoutingDecision:
    try:validate_routing_input(item)
    except ValueError as exc:return ProviderRoutingDecision(None,None,"blocked",(str(exc),),(),tuple(p.provider_id for p in provider_profiles),False,False,0,item.request_budget.maximum_requests_per_chunk,"unknown",item.cache_availability,item.verified_draft_available,False)
    if item.cache_availability:return ProviderRoutingDecision(None,None,"use_cached_result",("verified_cache_available",),(),(),False,False,0,item.request_budget.maximum_requests_per_chunk,"none",True,False,False)
    compat={};eligible=[];ineligible=[]
    for p in provider_profiles:
        c=evaluate_provider_compatibility(item,p,required_quality_contract_id=QUALITY_CONTRACT.contract_id,required_quality_contract_version=QUALITY_CONTRACT.version,required_prompt_contract_id="ntpe-literary-structured",required_prompt_contract_version="1.0");compat[p.provider_id]=c
        (eligible if c.status in {"compatible","manual_review_required"} else ineligible).append(p.provider_id)
    primary=next((p for p in provider_profiles if p.provider_id==routing_policy.primary_provider_id),None)
    if primary is None:return ProviderRoutingDecision(None,None,"blocked",("primary_provider_missing",),tuple(eligible),tuple(ineligible),False,False,0,item.request_budget.maximum_requests_per_chunk,"unknown",False,item.verified_draft_available,False)
    health=item.provider_health_evidence.get(primary.provider_id,"unknown"); planned=1 if item.translation_mode!="dual_pass" or item.verified_draft_available else 2;budget=calculate_request_budget(item,planned_requests=planned)
    if not budget["valid"]:return ProviderRoutingDecision(None,None,"blocked",tuple(budget["exceeded"]),tuple(eligible),tuple(ineligible),False,False,0,item.request_budget.maximum_requests_per_chunk,health,False,item.verified_draft_available,False)
    if health in {"unavailable","timeout_prone","rate_limited"} and item.verified_draft_available:return ProviderRoutingDecision(None,None,"reuse_verified_draft",("provider_health_"+health,),tuple(eligible),tuple(ineligible),False,False,0,item.request_budget.maximum_requests_per_chunk,health,False,True,False)
    c=compat[primary.provider_id]
    if c.status=="manual_review_required" or not item.manual_approval_granted:return ProviderRoutingDecision(primary.provider_id,primary.model_id,"manual_review_required",tuple(c.reasons+("first_provider_or_model_requires_approval",)),tuple(eligible),tuple(ineligible),False,False,planned,item.request_budget.maximum_requests_per_chunk,health,False,item.verified_draft_available,True)
    if not c.compatible:return ProviderRoutingDecision(None,None,"blocked",c.reasons,tuple(eligible),tuple(ineligible),False,False,0,item.request_budget.maximum_requests_per_chunk,health,False,item.verified_draft_available,False)
    return ProviderRoutingDecision(primary.provider_id,primary.model_id,"use_primary",("compatible_primary_within_budget",),tuple(eligible),tuple(ineligible),False,False,planned,item.request_budget.maximum_requests_per_chunk,health,False,False,False)


def build_provider_execution_plan(item:ProviderRoutingInput,decision:ProviderRoutingDecision,profile:ProviderProfile|None,*,routing_policy:ProviderRoutingPolicy=DEFAULT_ROUTING_POLICY)->ProviderExecutionPlan:
    blocked=decision.reasons if decision.decision in {"blocked","manual_review_required"} else ()
    identity=build_provider_route_identity(item,profile,routing_policy)["translation_cache_identity"] if profile else ""
    attempts=({"provider_id":profile.provider_id,"model_id":profile.model_id,"attempt":1},) if profile and decision.decision in {"use_primary","retry_same_provider","fallback_provider"} else ()
    return ProviderExecutionPlan(True,False,0,decision.selected_provider,decision.selected_model,attempts,(),decision.maximum_requests,item.timeout_budget.per_attempt_timeout_seconds,item.timeout_budget.maximum_chunk_wall_clock_seconds,identity,item.quality_policy_identity,item.semantic_policy_identity,decision.manual_approval_required,tuple(blocked))


def build_routing_evidence(item,decision,policy=DEFAULT_ROUTING_POLICY):
    payload={"input":asdict(item),"decision":asdict(decision),"policy":policy.version};fp=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
    return ProviderRoutingEvidence("route-"+fp[:20],fp,policy.version,decision.eligible_providers,decision.selected_provider,decision.ineligible_providers,tuple(x.evidence_id for x in item.provider_failure_history),calculate_request_budget(item,planned_requests=decision.estimated_requests),{},decision.decision,decision.reasons,item.created_at)
