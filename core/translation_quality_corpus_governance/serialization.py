from __future__ import annotations

import json
from collections.abc import Mapping

from .governance_model import ApprovalProvenance, AuditEvent, CorpusGovernanceRecord, DeprecationMetadata, RejectionMetadata, SourceEvidence, SupersessionMetadata
from .governance_validator import validate_governance_record
from .lifecycle import CorpusLifecycle


def serialize_governance_record(record: CorpusGovernanceRecord) -> str:
    validate_governance_record(record)
    return json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def deserialize_governance_record(payload: str | bytes | Mapping[str, object]) -> CorpusGovernanceRecord:
    raw = json.loads(payload) if isinstance(payload, (str, bytes, bytearray)) else dict(payload)
    required = {"case_id", "revision_id", "revision_number", "previous_revision_id", "status", "source_evidence", "approved_final_translation", "approval", "supersession", "deprecation", "rejection", "audit_history", "governance_schema_version"}
    if set(raw) != required:
        raise ValueError("governance record schema fields invalid")
    try:
        source = SourceEvidence(**raw["source_evidence"])
        approval = ApprovalProvenance(**raw["approval"]) if raw["approval"] is not None else None
        supersession = SupersessionMetadata(**raw["supersession"]) if raw["supersession"] is not None else None
        deprecation = DeprecationMetadata(**raw["deprecation"]) if raw["deprecation"] is not None else None
        rejection = RejectionMetadata(**raw["rejection"]) if raw["rejection"] is not None else None
        history = tuple(AuditEvent(**event) for event in raw["audit_history"])
        record = CorpusGovernanceRecord(
            case_id=raw["case_id"], revision_id=raw["revision_id"], revision_number=raw["revision_number"],
            previous_revision_id=raw["previous_revision_id"], status=CorpusLifecycle(raw["status"]),
            source_evidence=source, approved_final_translation=raw["approved_final_translation"], approval=approval,
            supersession=supersession, deprecation=deprecation, rejection=rejection, audit_history=history,
            governance_schema_version=raw["governance_schema_version"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("governance record payload invalid") from exc
    return validate_governance_record(record)

