from __future__ import annotations
import os,time
from typing import Any
from core.adaptive_context import ContextItem, build_adaptive_context, estimate_tokens
from core.adaptive_context_integration.utils import canonical_hash
from core.adaptive_context_prompt_anchor import anchored_context_text, replace_anchored_context, resolve_prompt_context_anchor
from .audit import write_canary_audit
from .model import CanaryRecord
from .registry import already_activated, append_canary_record
CANARY_VERSION="7.0.0-stage05"
TARGET_ENV="NTPE_TE_V7_ACE_CANARY_CHUNK"
BUDGET_ENV="NTPE_TE_V7_ACE_CANARY_CONTEXT_TOKENS"

def _integer_env(name:str,default:int,minimum:int=1)->int:
    try:return max(minimum,int(str(os.environ.get(name,default)).strip()))
    except (TypeError,ValueError):return default

def apply_prompt_package_canary(package:dict[str,object])->CanaryRecord|None:
    mode=str(os.environ.get("NTPE_TE_V7_ACE_MODE","disabled")).strip().lower()
    if mode!="canary":return None
    session=package.get("session",{}); session=session if isinstance(session,dict) else {}
    chunk_index=int(session.get("chunk_index",0) or 0); target=_integer_env(TARGET_ENV,2)
    before=canonical_hash(package); package_id=str(package.get("package_id",""))
    base={"content_redacted":True,"single_chunk_only":True,"prompt_exact_replacement_required":True}
    if chunk_index!=target or already_activated():
        rec=CanaryRecord(CANARY_VERSION,package_id,chunk_index,target,False,False,False,(),before,before,0,0,0,0.0,0,base)
        append_canary_record(rec);write_canary_audit(rec);return rec
    start=time.perf_counter_ns(); reasons=[]
    context=package.get("context",{}); prompt=package.get("prompt",{})
    if not isinstance(context,dict) or not isinstance(prompt,dict): reasons.append("invalid-package-shape")
    anchor=resolve_prompt_context_anchor(package)
    original=anchored_context_text(package,anchor)
    baseline=estimate_tokens(original) if original else 0
    candidate=""; candidate_tokens=0
    base={**base,"prompt_context_anchor_version":anchor.version,"prompt_context_anchor_strategy":anchor.strategy}
    if not reasons:
        if not anchor.addressable: reasons.append(anchor.reason or "prompt-context-anchor-unavailable")
        elif not original: reasons.append("prompt-context-anchor-content-unavailable")
        else:
            budget=min(max(1,_integer_env(BUDGET_ENV,128)),max(1,baseline-1))
            item=ContextItem("previous_chunk_tail","narrative",original,relevance=1.0,recency=1.0,continuity=1.0)
            result=build_adaptive_context((item,),model_context_limit=budget,reserved_output_tokens=0,requested_context_tokens=budget)
            if not result.admissible or result.fallback_required: reasons.extend(result.fallback_reasons or ("ace-inadmissible",))
            elif len(result.selected)!=1: reasons.append("no-safe-compressed-context")
            else:
                candidate=result.selected[0].content;candidate_tokens=result.selected[0].estimated_tokens
                if not candidate or candidate==original or candidate_tokens>=baseline: reasons.append("no-token-reduction")
    activated=not reasons
    if activated and not replace_anchored_context(package,anchor,candidate):
        reasons.append("prompt-context-anchor-replacement-failed");activated=False
    after=canonical_hash(package);elapsed=round((time.perf_counter_ns()-start)/1_000_000,3)
    if activated and after==before: reasons.append("payload-not-changed");activated=False
    if not activated and after!=before: raise RuntimeError("ACE canary fail-closed invariant violated")
    rec=CanaryRecord(CANARY_VERSION,package_id,chunk_index,target,True,activated,not activated,tuple(reasons),before,after,baseline,candidate_tokens if activated else baseline,max(0,baseline-candidate_tokens) if activated else 0,elapsed,0,base)
    append_canary_record(rec);write_canary_audit(rec);return rec
