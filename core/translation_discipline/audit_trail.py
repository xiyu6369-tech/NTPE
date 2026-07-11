from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
DISCIPLINE_AUDIT_VERSION = "6.0.0-stage07"
def _canonical_code(value: Any) -> str:
    code = str(value or "").strip().upper(); return code[3:] if code.startswith("V5_") else code
def _issue_records(unified_report: Mapping[str, Any]) -> list[dict[str, Any]]:
    records=[]
    for issue in unified_report.get("merged_issues") or []:
        if not isinstance(issue, Mapping): continue
        metadata=dict(issue.get("metadata") or {})
        records.append({"code":_canonical_code(issue.get("code") or issue.get("type")),"severity":str(issue.get("severity") or "").lower(),"source":issue.get("source"),"discipline_rule_code":metadata.get("discipline_rule_code"),"discipline_route":metadata.get("discipline_route"),"retry_required":bool(issue.get("retry_required")),"repairable":bool(issue.get("repairable"))})
    return records
@dataclass(frozen=True)
class DisciplineAuditTrail:
    payload: dict[str, Any]
    def to_metadata(self)->dict[str,Any]: return dict(self.payload)
def build_discipline_audit_trail(runtime_qa: Mapping[str, Any], *, initial_action: str, final_action: str, revalidated: bool, local_repair: Mapping[str, Any] | None=None)->DisciplineAuditTrail:
    qa=dict(runtime_qa or {}); unified=dict(qa.get("unified_quality_report") or {}); retry=dict(qa.get("adaptive_retry_decision") or unified.get("adaptive_retry_decision") or {}); repair=dict(local_repair or {}); issues=_issue_records(unified)
    active_rules=sorted({str(i.get("discipline_rule_code")) for i in issues if i.get("discipline_rule_code")})
    routes={}
    for i in issues: routes.setdefault(str(i.get("discipline_route") or "unmapped"),[]).append(str(i.get("code") or "UNKNOWN"))
    routes={k:sorted(set(v)) for k,v in sorted(routes.items())}
    policy=dict(qa.get("adaptive_retry_policy") or unified.get("adaptive_retry_policy") or {})
    budget=dict(policy.get("provider_call_budget") or {})
    return DisciplineAuditTrail({"schema_version":DISCIPLINE_AUDIT_VERSION,"orchestrator_version":str((qa.get("discipline_runtime_orchestrator") or {}).get("version") or "6.0.0-stage06"),"initial_action":str(initial_action),"final_action":str(final_action),"revalidated":bool(revalidated),"quality":{"score":int(unified.get("score") or 0),"decision":str(unified.get("decision") or qa.get("decision") or "runtime_error"),"final_reason":str(unified.get("final_reason") or retry.get("reason") or ""),"issue_count":len(issues),"issues":issues},"discipline":{"active_rule_codes":active_rules,"routes":routes},"local_repair":{"changed":bool(repair.get("changed")),"attempted_codes":list(repair.get("attempted_codes") or []),"repaired_codes":list(repair.get("repaired_codes") or []),"unresolved_codes":list(repair.get("unresolved_codes") or []),"action_count":len(repair.get("actions") or []),"actions":list(repair.get("actions") or [])},"retry_decision":{"version":retry.get("version"),"action":retry.get("action"),"reason":retry.get("reason"),"provider_retry_required":bool(retry.get("provider_retry_required")),"provider_retry_codes":list(retry.get("provider_retry_codes") or []),"warning_codes":list(retry.get("warning_codes") or [])},"adaptive_retry_policy":{"version":policy.get("version"),"retry_tier":policy.get("tier"),"retry_evidence":list(policy.get("retry_evidence") or []),"targeted_unit_count":len(policy.get("targeted_retry_units") or []),"full_retry_reason":policy.get("reason") if policy.get("tier")=="full_retry" else "","provider_call_budget":{"limit":int(budget.get("limit") or 0),"used":int(budget.get("used") or 0),"remaining":int(budget.get("remaining") or 0)},"fallback_reason":policy.get("reason") if policy.get("fallback_action") else "","selected_attempt":(qa.get("best_attempt_selection") or {}).get("selected_qa_attempt"),"selected_candidate":(qa.get("best_attempt_selection") or {}).get("selected_candidate")}})
