from __future__ import annotations

from core.adaptive_context_authorized_provider_harness import AuthorizedProviderHarnessResult

from .config import ProviderEvidencePipelineConfig
from .model import ProviderEvidenceArtifact
from .normalizer import normalize_attempt

_SUCCESS = {"success", "accepted"}


def collect_provider_evidence_artifact(
    result: AuthorizedProviderHarnessResult,
    config: ProviderEvidencePipelineConfig,
) -> ProviderEvidenceArtifact:
    blockers = config.validate()
    if blockers:
        raise ValueError(",".join(blockers))
    session = result.invocation.session
    records = tuple(session.evidence.records)
    attempts = tuple(normalize_attempt(record) for record in records)
    first = records[0] if records else None
    resume_excluded = bool(session.evidence.excluded_resume_chunks)
    mock_consistent = (
        result.execution_provenance == "fake"
        and not result.real_provider_execution
        and not result.invocation.real_provider_execution
        and all(not row.real_provider_execution for row in records)
    )
    real_consistent = (
        result.execution_provenance == "real"
        and result.real_provider_execution
        and result.invocation.real_provider_execution
        and result.invocation.authorization_recorded
        and bool(records)
        and all(row.real_provider_execution for row in records)
    )
    provenance_ok = mock_consistent if config.declared_provenance == "mock" else real_consistent

    limitations: list[str] = []
    if not provenance_ok:
        limitations.append("execution-provenance-mismatch")
    if not records:
        limitations.append("no-provider-request-evidence")
    if any(not row.timing_complete for row in records):
        limitations.append("provider-timing-evidence-incomplete")
    if any(
        row.token_usage.estimated_input_tokens <= 0
        or row.token_usage.estimated_output_tokens <= 0
        for row in records
    ):
        limitations.append("provider-token-evidence-incomplete")
    if not session.summary.payload_preserved:
        limitations.append("payload-not-preserved")
    if not session.summary.prompt_preserved:
        limitations.append("prompt-not-preserved")
    if resume_excluded:
        limitations.append("resume-chunk-excluded")
    if any(row.suspicious_short_output for row in records):
        limitations.append("suspicious-short-output")
    if any(row.status not in _SUCCESS for row in records):
        limitations.append("provider-run-incomplete")

    complete = bool(records) and not any(item in limitations for item in (
        "provider-timing-evidence-incomplete",
        "provider-token-evidence-incomplete",
        "payload-not-preserved",
        "prompt-not-preserved",
    ))
    ready = (
        provenance_ok
        and config.declared_provenance == "real"
        and complete
        and not resume_excluded
        and not any(row.suspicious_short_output or row.status not in _SUCCESS for row in records)
    )
    if not provenance_ok:
        status = "rejected_provenance"
    elif resume_excluded and not records:
        status = "excluded_resume"
    elif ready:
        status = "ready_for_benchmark"
    elif complete and config.declared_provenance == "mock":
        status = "evidence_complete_mock_only"
    elif complete:
        status = "evidence_complete_provider_limited"
    else:
        status = "evidence_incomplete"

    return ProviderEvidenceArtifact(
        session_id=result.session_id,
        chunk_identity=(
            f"{first.set_name}:{first.chunk_index}" if first is not None else "excluded-resume"
        ),
        source_fingerprint=first.source_hash if first is not None else "",
        chunk_fingerprint=first.chunk_hash if first is not None else "",
        model=first.model if first is not None else result.invocation.model,
        attempts=attempts,
        status=status,
        evidence_provenance=config.declared_provenance,
        transport_provenance=result.execution_provenance,
        evidence_complete=complete,
        ready_for_benchmark=ready,
        payload_preserved=session.summary.payload_preserved,
        prompt_preserved=session.summary.prompt_preserved,
        resume_excluded=resume_excluded,
        short_output_suspicion=any(row.suspicious_short_output for row in records),
        limitations=tuple(limitations),
    )
