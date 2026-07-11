from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
EVIDENCE_AUDIT_VERSION = "6.0.0-stage11.5"
def _as_dict(value: Any) -> dict[str, Any]: return dict(value) if isinstance(value, Mapping) else {}
def _merge_validation_records(targeted_retry: Mapping[str, Any]) -> list[dict[str, Any]]:
    records=[]
    for unit in targeted_retry.get("units") or []:
        if not isinstance(unit, Mapping): continue
        validation=_as_dict(unit.get("merge_validation"))
        if validation: records.append({"unit_id":str(unit.get("unit_id") or ""),"reason_codes":list(unit.get("reason_codes") or []),"result":str(unit.get("result") or ""),"validation":validation})
    return records
@dataclass(frozen=True)
class EvidenceAuditTrail:
    payload: dict[str, Any]
    def to_metadata(self)->dict[str,Any]: return dict(self.payload)
def build_evidence_audit_trail(runtime_qa: Mapping[str, Any]) -> EvidenceAuditTrail:
    qa=_as_dict(runtime_qa); unified=_as_dict(qa.get("unified_quality_report")); integration=_as_dict(qa.get("evidence_retry_integration") or unified.get("evidence_retry_integration")); policy=_as_dict(qa.get("adaptive_retry_policy") or unified.get("adaptive_retry_policy")); targeted=_as_dict(qa.get("targeted_retry_execution") or qa.get("targeted_retry")); retry_evidence=list(policy.get("retry_evidence") or []); targeted_units=list(policy.get("targeted_retry_units") or []); merge_records=_merge_validation_records(targeted); reliable_count=sum(1 for x in retry_evidence if isinstance(x,Mapping) and x.get("reliable")); unsafe_merges=sum(1 for x in merge_records if not bool(_as_dict(x.get("validation")).get("accepted")))
    return EvidenceAuditTrail({"version":EVIDENCE_AUDIT_VERSION,"alignment":{"version":integration.get("alignment_engine_version"),"reliable":bool(integration.get("alignment_reliable")),"evidence_count":int(integration.get("evidence_count") or 0),"reliable_evidence_count":int(integration.get("reliable_evidence_count") or 0),"applied_issue_codes":list(integration.get("applied_issue_codes") or []),"skipped_issue_codes":list(integration.get("skipped_issue_codes") or []),"fail_closed":bool(integration.get("fail_closed",True))},"retry_evidence":{"count":len(retry_evidence),"reliable_count":reliable_count,"items":retry_evidence},"targeted_retry":{"tier":policy.get("tier"),"planned_unit_count":len(targeted_units),"executed_unit_count":len(targeted.get("units") or []),"result":targeted.get("result"),"provider_calls_used":int(targeted.get("provider_calls_used") or 0),"units":list(targeted.get("units") or [])},"merge_validation":{"version":"6.0.0-stage11.4","record_count":len(merge_records),"unsafe_count":unsafe_merges,"records":merge_records,"fail_closed":True},"trace_complete":bool(integration) and (policy.get("tier")!="targeted_retry" or bool(targeted_units)),"runtime_integrated":True})
