from __future__ import annotations

import hashlib
from pathlib import Path

from .integration_model import IntegrityVerificationResult, QualityFrameworkIntegration
from .references import resolve_reference


def _actual_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_quality_framework_integrity(record: QualityFrameworkIntegration, *, root: str | Path) -> IntegrityVerificationResult:
    references = (
        ("11.1", record.defects_reference, record.defects_sha256),
        ("11.2", record.metrics_reference, record.metrics_sha256),
        ("11.3", record.review_artifact_reference, record.review_artifact_sha256),
        ("11.4", record.improvement_plan_reference, record.improvement_plan_sha256),
        ("11.5", record.human_decision_reference, record.human_decision_sha256),
        ("11.6", record.corpus_governance_reference, record.corpus_governance_sha256),
        ("golden_corpus", record.golden_corpus_reference, record.golden_corpus_sha256),
    )
    for stage, reference, expected in references:
        actual = _actual_sha256(resolve_reference(root, reference))
        if actual != expected:
            return IntegrityVerificationResult(False, stage, reference, expected, actual)
    return IntegrityVerificationResult(True)

