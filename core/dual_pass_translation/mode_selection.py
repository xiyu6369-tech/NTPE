from __future__ import annotations
from dataclasses import replace
from .draft_contract import evaluate_draft_eligibility
from .models import *
from .validation import DualPassValidationError,validate_trigger
_VALID_TRIGGER_TYPES=set(TriggerType)-{TriggerType.NO_TRIGGER}
_SEVERITY_RANK={Severity.INFO:0,Severity.NONBLOCKING:1,Severity.BLOCKING:2,Severity.CRITICAL:3}
def create_polish_trigger(*,trigger_id,trigger_type,evidence,confidence,severity,scope,estimated_quality_value,estimated_cost,eligible=True):
    kind=trigger_type if isinstance(trigger_type,TriggerType) else TriggerType(trigger_type)
    if kind==TriggerType.NO_TRIGGER:eligible=False
    trigger=PolishTrigger(trigger_id,kind,tuple(evidence),float(confidence),severity if isinstance(severity,Severity) else Severity(severity),scope,float(estimated_quality_value),int(estimated_cost),bool(eligible));validate_trigger(trigger)
    if not trigger.evidence and kind!=TriggerType.HUMAN_REQUESTED:raise DualPassValidationError("trigger requires direct evidence")
    return trigger
def evaluate_polish_triggers(triggers):
    unique={}
    for trigger in triggers:
        validate_trigger(trigger);key=(trigger.trigger_type.value,trigger.scope.scope_type.value,trigger.scope.start_identifier,trigger.scope.end_identifier)
        current=unique.get(key)
        if current is None or (trigger.eligible,_SEVERITY_RANK[trigger.severity],trigger.confidence,trigger.trigger_id)>(current.eligible,_SEVERITY_RANK[current.severity],current.confidence,current.trigger_id):unique[key]=trigger
    return tuple(sorted((x for x in unique.values() if x.eligible and x.trigger_type in _VALID_TRIGGER_TYPES),key=lambda x:(x.scope.scope_type.value,x.trigger_type.value,x.trigger_id)))
def select_translation_mode(draft,triggers,*,provider_policy,cost_policy,timeout_policy,quality_policy):
    eligibility=evaluate_draft_eligibility(draft,expected_source_hash=provider_policy.get("expected_source_hash"),allow_nonblocking=quality_policy.get("allow_nonblocking_draft",False));evaluated=evaluate_polish_triggers(triggers);health=ProviderHealth(provider_policy.get("health","unknown"));reasons=[]
    if not eligibility["eligible"]:return DualPassDecision(TranslationMode.BLOCKED,"blocked",eligibility["reasons"],(),0,0,0,1.0,"block_output")
    if not provider_policy.get("rollback_available",True):return DualPassDecision(TranslationMode.SINGLE_PASS,"single_pass",("rollback_baseline_unavailable",),(),1,0,0,0.0,"verified_draft")
    if not evaluated:return DualPassDecision(TranslationMode.SINGLE_PASS,"single_pass",("no_eligible_polish_trigger",),(),1,0,0,0.0,"verified_draft")
    if health==ProviderHealth.UNAVAILABLE or not cost_policy.get("allow_second_request",True):return DualPassDecision(TranslationMode.SINGLE_PASS,"single_pass",("second_request_disallowed",health.value),tuple(x.trigger_id for x in evaluated),1,0,0,1.0,"verified_draft")
    local=[x for x in evaluated if x.scope.scope_type not in {PolishScopeType.FULL_CHUNK,PolishScopeType.NONE}];full=[x for x in evaluated if x.scope.scope_type==PolishScopeType.FULL_CHUNK];human=any(x.trigger_type==TriggerType.HUMAN_REQUESTED for x in evaluated);risk=float(timeout_policy.get("timeout_risk",0.5))
    if local and (health in {ProviderHealth.HEALTHY,ProviderHealth.DEGRADED} or human):mode=TranslationMode.SELECTIVE_POLISH;why="local_high_value_trigger"
    elif full and health==ProviderHealth.HEALTHY and risk<=float(timeout_policy.get("maximum_dual_pass_risk",0.3)):mode=TranslationMode.DUAL_PASS;why="verified_full_chunk_value"
    else:mode=TranslationMode.SINGLE_PASS;why="provider_or_timeout_risk"
    requests=2 if mode in {TranslationMode.DUAL_PASS,TranslationMode.SELECTIVE_POLISH} else 1
    return DualPassDecision(mode,mode.value,(why,),tuple(x.trigger_id for x in evaluated),requests,sum(x.estimated_cost for x in evaluated),int(cost_policy.get("estimated_output_tokens",0)),risk,"rollback_to_verified_draft")
