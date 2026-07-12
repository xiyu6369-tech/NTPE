from __future__ import annotations
import json
from pathlib import Path
from .registry import canary_records
CANARY_REPORT_VERSION="7.0.0-stage05"
def build_canary_report(stage:str="TE-v7.0-Stage05") -> dict[str,object]:
    rows=canary_records(); attempted=[r for r in rows if r.attempted]; active=[r for r in rows if r.activated]
    blockers=[]
    if len(active)>1:blockers.append("multiple-canary-activations")
    if any(r.provider_calls_added for r in rows):blockers.append("provider-calls-added")
    return {"version":CANARY_REPORT_VERSION,"stage":stage,"status":"pass" if not blockers else "fail","ready":not blockers,
    "records":len(rows),"attempted_records":len(attempted),"activated_records":len(active),"fallback_records":sum(1 for r in attempted if r.fallback_used),
    "estimated_tokens_saved":sum(r.estimated_tokens_saved for r in active),"provider_calls_added":sum(r.provider_calls_added for r in rows),
    "blockers":blockers,"metadata":{"content_redacted":True,"single_chunk_only":True,"automatic_expansion":False,"provider_timeout_is_not_ace_failure":True}}
def write_canary_report(report:dict[str,object],path:str|Path)->Path:
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8");return p
