from __future__ import annotations

from .model import EVIDENCE_STATUSES, ProviderEvidenceArtifact


def validate_provider_evidence_artifact(artifact: ProviderEvidenceArtifact) -> tuple[str, ...]:
    blockers: list[str] = []
    if artifact.status not in EVIDENCE_STATUSES:
        blockers.append("provider-evidence-artifact-status-invalid")
    if artifact.evidence_provenance not in {"mock", "real"}:
        blockers.append("provider-evidence-artifact-provenance-invalid")
    if artifact.evidence_provenance == "mock" and artifact.transport_provenance != "fake":
        blockers.append("provider-evidence-artifact-fake-bridge-mismatch")
    if artifact.evidence_provenance == "real" and artifact.transport_provenance != "real":
        blockers.append("provider-evidence-artifact-real-provenance-mismatch")
    if artifact.ready_for_benchmark and artifact.status != "ready_for_benchmark":
        blockers.append("provider-evidence-artifact-ready-status-mismatch")
    if artifact.ready_for_benchmark and (
        artifact.evidence_provenance != "real"
        or artifact.resume_excluded
        or artifact.short_output_suspicion
        or not artifact.evidence_complete
    ):
        blockers.append("provider-evidence-artifact-readiness-contract-invalid")
    if artifact.status == "evidence_complete_mock_only" and artifact.ready_for_benchmark:
        blockers.append("provider-evidence-artifact-mock-ready-forbidden")
    if artifact.baseline_candidate_compared:
        blockers.append("provider-evidence-artifact-comparison-forbidden")
    if any((
        artifact.production_readiness_evaluated,
        artifact.rollout_readiness_evaluated,
        artifact.translation_quality_evaluated,
    )):
        blockers.append("provider-evidence-artifact-readiness-evaluation-forbidden")
    return tuple(blockers)
