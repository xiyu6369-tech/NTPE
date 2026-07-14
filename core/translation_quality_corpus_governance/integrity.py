from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from pathlib import Path

from core.translation_quality_review_decision import HumanReviewDecision, verify_review_decision_integrity

from .governance_model import CorpusGovernanceRecord

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_corpus_integrity(
    record: CorpusGovernanceRecord,
    *,
    source_artifact: str | Path,
    source_text: str | None = None,
    decision: HumanReviewDecision | None = None,
    decision_artifacts: Mapping[str, str | Path] | None = None,
) -> bool:
    evidence = record.source_evidence
    if sha256_file(source_artifact) != evidence.source_artifact_sha256:
        raise ValueError("source artifact integrity mismatch")
    if source_text is not None and sha256_text(source_text) != evidence.source_text_sha256:
        raise ValueError("source text integrity mismatch")
    if decision is not None:
        if decision_artifacts is None:
            raise ValueError("decision artifact references are required")
        verify_review_decision_integrity(decision, decision_artifacts)
        approval = record.approval
        if approval is not None and (
            approval.approval_decision_id != decision.decision_id
            or approval.review_artifact_sha256 != decision.review_artifact_sha256
            or approval.metrics_sha256 != decision.metrics_sha256
            or approval.defects_sha256 != decision.defects_sha256
        ):
            raise ValueError("approval decision provenance mismatch")
    return True

