from __future__ import annotations

from core.adaptive_context_authorized_provider_cli import AuthorizedProviderCliResult
from core.adaptive_context_provider_evidence_pipeline import ProviderEvidenceArtifact


def validate_fake_transport_chain(
    cli_result: AuthorizedProviderCliResult,
    evidence: ProviderEvidenceArtifact,
) -> tuple[str, ...]:
    blockers: list[str] = []
    harness = cli_result.harness_result
    session = harness.invocation.session
    if harness.execution_provenance != "fake" or evidence.transport_provenance != "fake":
        blockers.append("provider-execution-freeze-fake-provenance-required")
    if evidence.evidence_provenance != "mock" or evidence.status == "ready_for_benchmark":
        blockers.append("provider-execution-freeze-real-provenance-forbidden")
    if harness.real_provider_execution or harness.invocation.real_provider_execution:
        blockers.append("provider-execution-freeze-real-provider-execution-forbidden")
    if cli_result.network_requests != 0:
        blockers.append("provider-execution-freeze-network-request-detected")
    if not harness.authorization_confirmed:
        blockers.append("provider-execution-freeze-authorization-not-confirmed")
    if not harness.single_chunk_only or not harness.single_controlled_session:
        blockers.append("provider-execution-freeze-session-boundary-invalid")
    if not session.summary.payload_preserved or not session.summary.prompt_preserved:
        blockers.append("provider-execution-freeze-input-mutation-detected")
    if not evidence.content_redacted or not harness.content_redacted:
        blockers.append("provider-execution-freeze-content-redaction-required")
    if any((
        harness.comparison_evaluated,
        harness.readiness_evaluated,
        cli_result.comparison_evaluated,
        cli_result.readiness_evaluated,
        evidence.baseline_candidate_compared,
        evidence.production_readiness_evaluated,
        evidence.rollout_readiness_evaluated,
        evidence.translation_quality_evaluated,
    )):
        blockers.append("provider-execution-freeze-evaluation-forbidden")
    return tuple(blockers)
