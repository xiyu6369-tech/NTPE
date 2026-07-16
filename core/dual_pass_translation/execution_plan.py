from __future__ import annotations
import hashlib,json
from dataclasses import asdict
from .models import *
def build_dual_pass_execution_plan(decision,*,triggers=(),cost_estimate,cache_candidates=(),prepare_only=True):
    scopes=[x.scope for x in triggers if x.eligible];scope=scopes[0] if decision.mode==TranslationMode.SELECTIVE_POLISH and scopes else (next((x for x in scopes if x.scope_type==PolishScopeType.FULL_CHUNK),None) if decision.mode==TranslationMode.DUAL_PASS else None)
    blocked=decision.reasons if decision.mode==TranslationMode.BLOCKED else ()
    return DualPassExecutionPlan(decision.mode,decision.mode!=TranslationMode.BLOCKED,decision.mode in {TranslationMode.DUAL_PASS,TranslationMode.SELECTIVE_POLISH},scope,decision.mode in {TranslationMode.DUAL_PASS,TranslationMode.SELECTIVE_POLISH},decision.fallback_policy=="rollback_to_verified_draft",cost_estimate.request_count,cost_estimate.total_tokens,cost_estimate.worst_case_requests,tuple(cache_candidates),tuple(blocked),prepare_only,False)
def create_execution_evidence(plan):
    body=json.dumps(asdict(plan),ensure_ascii=False,sort_keys=True,default=lambda x:x.value if hasattr(x,"value") else str(x),separators=(",",":"));return DualPassExecutionEvidence(hashlib.sha256(body.encode()).hexdigest(),False,False,0,False,({"event":"plan_prepared","prepare_only":plan.prepare_only},))
