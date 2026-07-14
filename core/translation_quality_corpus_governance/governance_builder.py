from __future__ import annotations

import hashlib

from .governance_model import AuditEvent, CorpusGovernanceRecord, SourceEvidence
from .governance_validator import validate_governance_record
from .lifecycle import CorpusLifecycle
from .provenance import GOVERNANCE_SCHEMA_VERSION, validate_human_actor


def build_governance_record(
    *,
    case_id: str,
    source_text_excerpt: str | None,
    source_language: str,
    target_language: str,
    source_text_sha256: str,
    source_artifact_reference: str,
    source_artifact_sha256: str,
    created_at: str,
    created_by: str,
    creation_reason: str,
) -> CorpusGovernanceRecord:
    validate_human_actor(created_by)
    identity = hashlib.sha256(f"{case_id}\n{source_text_sha256}\n{created_at}".encode("utf-8")).hexdigest()[:16].upper()
    revision_id = f"TQ-GOV-{identity}-R001"
    evidence = SourceEvidence(source_text_excerpt, source_language, target_language, source_text_sha256, source_artifact_reference, source_artifact_sha256, created_at, GOVERNANCE_SCHEMA_VERSION)
    event = AuditEvent("created", created_by, creation_reason, created_at, None, CorpusLifecycle.DRAFT.value)
    return validate_governance_record(CorpusGovernanceRecord(
        case_id, revision_id, 1, None, CorpusLifecycle.DRAFT, evidence, None, None,
        None, None, None, (event,), GOVERNANCE_SCHEMA_VERSION,
    ))

