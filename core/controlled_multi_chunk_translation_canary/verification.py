"""Fail-closed verification for completed Stage 7.4 executions."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .checkpoint import read_checkpoint
from .errors import ControlledMultiChunkVerificationError
from .models import (
    MultiChunkCanaryRequest, MultiChunkResult, MultiChunkVerificationResult,
)
from .policy import CHUNK_COUNT, COMBINED_BOUNDARY


def verify_multi_chunk_result(
    request: MultiChunkCanaryRequest,
    result: MultiChunkResult,
    *,
    artifact_root: str | Path,
    raise_on_error: bool = False,
) -> MultiChunkVerificationResult:
    reasons: list[str] = []
    root = Path(artifact_root).resolve()
    if result.request_id != request.request_id:
        reasons.append("request-id-mismatch")
    exact = (
        result.chunks_planned == result.chunks_started == result.chunks_completed
        == result.provider_requests == result.provider_attempts
        == result.provider_successes == result.translation_executions
        == result.chunk_outputs_written == result.checkpoints_written == CHUNK_COUNT
    )
    if not exact or result.combined_output_written != 1:
        reasons.append("success-counters-invalid")
    if any((
        result.retries, result.fallbacks, result.parallel_requests,
        result.automatic_rollouts, result.formal_output_replacements,
        result.resume_execution_attempts, result.cache_mutations,
    )):
        reasons.append("zero-policy-violated")
    if len(result.chunk_evidence) != CHUNK_COUNT:
        reasons.append("chunk-evidence-count-invalid")
    outputs: list[str] = []
    for evidence in result.chunk_evidence:
        path = (root / evidence.output_artifact_path).resolve()
        if root not in path.parents or not path.is_file():
            reasons.append("chunk-output-missing")
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != evidence.output_fingerprint:
            reasons.append("chunk-output-fingerprint-mismatch")
        outputs.append(path.read_text(encoding="utf-8"))
        checkpoint = root / f"checkpoint-{evidence.index:03d}.json"
        try:
            record = read_checkpoint(checkpoint)
            if record.completed_chunk_count != evidence.index:
                reasons.append("checkpoint-order-invalid")
        except ControlledMultiChunkVerificationError:
            reasons.append("checkpoint-invalid")
        except Exception:
            reasons.append("checkpoint-invalid")
    combined_path = (root / result.combined_output_path).resolve()
    expected_combined = COMBINED_BOUNDARY.join(outputs)
    if root not in combined_path.parents or not combined_path.is_file():
        reasons.append("combined-output-missing")
    else:
        combined = combined_path.read_text(encoding="utf-8")
        if combined != expected_combined:
            reasons.append("combined-output-order-mismatch")
        if hashlib.sha256(combined_path.read_bytes()).hexdigest() != result.combined_output_fingerprint:
            reasons.append("combined-output-fingerprint-mismatch")
    verification = MultiChunkVerificationResult(
        valid=not reasons,
        reason_codes=tuple(dict.fromkeys(reasons)),
        request_id=request.request_id,
        result_fingerprint=result.result_fingerprint,
    )
    if raise_on_error and not verification.valid:
        raise ControlledMultiChunkVerificationError(",".join(verification.reason_codes))
    return verification
