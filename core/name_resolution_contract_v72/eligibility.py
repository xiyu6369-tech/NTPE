from __future__ import annotations

from .models import NameResolutionRecord
from .normalization import contains_hangul, contains_latin, is_valid_zh_hant_name_shape, script_profile


def mapping_exclusion_reasons(record: NameResolutionRecord) -> tuple[str, ...]:
    reasons: list[str] = []
    target = record.approved_zh_hant_name or ""
    if not record.source_name.strip(): reasons.append("empty_source_name")
    if not target: reasons.append("missing_approved_zh_hant_name")
    if record.approval_status != "approved": reasons.append("approval_not_approved")
    if target and contains_hangul(target): reasons.append("target_contains_hangul")
    if target and contains_latin(target): reasons.append("target_contains_latin")
    if target and not is_valid_zh_hant_name_shape(target): reasons.append("invalid_zh_hant_name_shape")
    profile = script_profile(target)
    if sum(profile.values()) > 1: reasons.append("mixed_script_target")
    if target and record.source_name == target: reasons.append("source_target_identical")
    if not record.evidence_ids: reasons.append("missing_traceable_evidence")
    if record.approval_status == "rejected" or record.mapping_status == "rejected_target_mapping":
        reasons.append("rejected_mapping")
    if record.expired or record.mapping_status == "expired_target_mapping": reasons.append("expired_mapping")
    if record.superseded: reasons.append("superseded_mapping")
    if record.conflict_state or record.mapping_status == "conflicting_target_mapping": reasons.append("conflicting_mapping")
    if record.mapping_status != "approved_target_mapping": reasons.append("not_approved_target_mapping")
    return tuple(dict.fromkeys(reasons))


def is_prompt_eligible(record: NameResolutionRecord) -> bool:
    return record.prompt_eligible and not mapping_exclusion_reasons(record)
