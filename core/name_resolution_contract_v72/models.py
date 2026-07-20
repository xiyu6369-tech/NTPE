from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from .normalization import is_valid_zh_hant_name_shape, normalize_source_name
from .serialization import deterministic_sha256


MappingStatus = Literal[
    "approved_target_mapping", "identity_only", "missing_approved_target_name",
    "conflicting_target_mapping", "rejected_target_mapping", "expired_target_mapping",
    "unresolved",
]
MappingSource = Literal["corpus", "glossary", "character_memory", "human_review", "none"]
ApprovalStatus = Literal["approved", "unreviewed", "rejected"]


@dataclass(frozen=True)
class NameResolutionRecord:
    source_name: str
    source_language: str
    normalized_source_name: str
    identity_transliteration: str | None
    approved_zh_hant_name: str | None
    mapping_status: MappingStatus
    mapping_source: MappingSource
    evidence_ids: tuple[str, ...]
    approval_status: ApprovalStatus
    prompt_eligible: bool
    target_script_valid: bool
    unresolved_reason: str | None
    conflict_state: bool
    superseded: bool
    expired: bool
    deterministic_fingerprint: str

    @classmethod
    def create(
        cls,
        *,
        source_name: str,
        source_language: str = "ko",
        identity_transliteration: str | None = None,
        approved_zh_hant_name: str | None = None,
        mapping_status: MappingStatus = "unresolved",
        mapping_source: MappingSource = "none",
        evidence_ids: tuple[str, ...] = (),
        approval_status: ApprovalStatus = "unreviewed",
        unresolved_reason: str | None = None,
        conflict_state: bool = False,
        superseded: bool = False,
        expired: bool = False,
    ) -> "NameResolutionRecord":
        normalized = normalize_source_name(source_name)
        target_valid = bool(approved_zh_hant_name and is_valid_zh_hant_name_shape(approved_zh_hant_name))
        eligible = bool(
            mapping_status == "approved_target_mapping"
            and approval_status == "approved"
            and target_valid
            and evidence_ids
            and not conflict_state
            and not superseded
            and not expired
        )
        payload = {
            "source_name": source_name, "source_language": source_language,
            "normalized_source_name": normalized,
            "identity_transliteration": identity_transliteration,
            "approved_zh_hant_name": approved_zh_hant_name,
            "mapping_status": mapping_status, "mapping_source": mapping_source,
            "evidence_ids": list(evidence_ids), "approval_status": approval_status,
            "prompt_eligible": eligible, "target_script_valid": target_valid,
            "unresolved_reason": unresolved_reason, "conflict_state": conflict_state,
            "superseded": superseded, "expired": expired,
        }
        return cls(**payload, deterministic_fingerprint=deterministic_sha256(payload))

    def with_conflict(self) -> "NameResolutionRecord":
        payload = {
            "source_name": self.source_name, "source_language": self.source_language,
            "identity_transliteration": self.identity_transliteration,
            "approved_zh_hant_name": None, "mapping_status": "conflicting_target_mapping",
            "mapping_source": "none", "evidence_ids": self.evidence_ids,
            "approval_status": "unreviewed", "unresolved_reason": "conflicting_approved_target_mappings",
            "conflict_state": True, "superseded": False, "expired": False,
        }
        return type(self).create(**payload)

    def to_dict(self) -> dict[str, object]:
        data = dict(self.__dict__)
        data["evidence_ids"] = list(self.evidence_ids)
        return data
